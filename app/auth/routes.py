from datetime import timedelta
from email.message import EmailMessage
import smtplib
from urllib.parse import urljoin, urlparse

from flask import current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from ..extensions import db
from ..models import User, utcnow
from . import bp


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="quizmaster-password-reset")


def _reset_token(user: User) -> str:
    return _serializer().dumps(
        {"user_id": user.id, "generation": user.reset_generation}
    )


def _safe_next(target: str | None) -> bool:
    if not target:
        return False
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return redirect_url.scheme in {"http", "https"} and host_url.netloc == redirect_url.netloc


def _send_reset_email(user: User, token: str) -> None:
    config = current_app.config
    if not all((config.get("MAIL_SERVER"), config.get("MAIL_DEFAULT_SENDER"))):
        return
    message = EmailMessage()
    message["Subject"] = "Reset your QuizMaster password"
    message["From"] = config["MAIL_DEFAULT_SENDER"]
    message["To"] = user.email
    message.set_content(
        "A password reset was requested for your QuizMaster account.\n\n"
        f"Use this link within one hour: {url_for('auth.reset_password', token=token, _external=True)}\n\n"
        "If you did not request this, you can ignore this email."
    )
    with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"], timeout=10) as server:
        if config.get("MAIL_USE_TLS"):
            server.starttls()
        if config.get("MAIL_USERNAME"):
            server.login(config["MAIL_USERNAME"], config.get("MAIL_PASSWORD") or "")
        server.send_message(message)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("student.dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or len(name) > 100:
            flash("Enter a name of 1 to 100 characters.", "error")
        elif len(email) > 254 or "@" not in email:
            flash("Enter a valid email address.", "error")
        elif len(password) < 10:
            flash("Use a password with at least 10 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
        else:
            user = User(name=name, email=email, role="student")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            session.clear()
            login_user(user)
            flash("Your account is ready.", "success")
            return redirect(url_for("student.dashboard"))
    return render_template("auth/form.html", page_title="Create your account", form_kind="register")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("student.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        now = utcnow()
        if user and user.active and user.locked_until and user.locked_until > now:
            flash("Unable to sign in right now. Try again later.", "error")
        elif user and user.active and user.check_password(password):
            user.failed_logins = 0
            user.locked_until = None
            db.session.commit()
            session.clear()
            login_user(user, remember=request.form.get("remember") == "on")
            flash("Welcome back.", "success")
            target = request.args.get("next")
            return redirect(target if _safe_next(target) else url_for("student.dashboard"))
        else:
            if user and user.active:
                user.failed_logins += 1
                if user.failed_logins >= 5:
                    user.failed_logins = 0
                    user.locked_until = now + timedelta(minutes=15)
                db.session.commit()
            flash("Email or password was not recognized.", "error")
    return render_template("auth/form.html", page_title="Sign in", form_kind="login")


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email, active=True).first()
        if user:
            token = _reset_token(user)
            try:
                _send_reset_email(user, token)
            except (OSError, smtplib.SMTPException):
                current_app.logger.exception("Password reset email delivery failed.")
        flash("If an active account matches that email, and email delivery is configured, reset instructions will be sent.", "info")
        return redirect(url_for("auth.forgot_password"))
    return render_template("auth/form.html", page_title="Reset your password", form_kind="forgot")


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    try:
        payload = _serializer().loads(token, max_age=3600)
    except (BadSignature, SignatureExpired):
        flash("That reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))
    if not isinstance(payload, dict) or not isinstance(payload.get("user_id"), int):
        flash("That reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))
    user_id = payload["user_id"]
    user = db.session.get(User, user_id)
    if not user or not user.active or payload.get("generation") != user.reset_generation:
        flash("That reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))
    if request.method == "POST":
        password = request.form.get("password", "")
        if len(password) < 10:
            flash("Use a password with at least 10 characters.", "error")
        else:
            user.set_password(password)
            user.failed_logins = 0
            user.locked_until = None
            user.reset_generation += 1
            db.session.commit()
            flash("Your password has been changed. Please sign in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/form.html", page_title="Choose a new password", form_kind="reset")


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "profile":
            name = request.form.get("name", "").strip()
            if not name or len(name) > 100:
                flash("Name must be between 1 and 100 characters.", "error")
            else:
                current_user.name = name
                db.session.commit()
                flash("Profile updated.", "success")
        elif action == "password":
            old_password = request.form.get("old_password", "")
            password = request.form.get("password", "")
            if not current_user.check_password(old_password):
                flash("Current password is incorrect.", "error")
            elif len(password) < 10:
                flash("Use a password with at least 10 characters.", "error")
            else:
                current_user.set_password(password)
                current_user.reset_generation += 1
                db.session.commit()
                flash("Password changed.", "success")
        else:
            flash("Unsupported profile action.", "error")
        return redirect(url_for("auth.profile"))
    return render_template("auth/profile.html")
