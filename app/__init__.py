import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template
from sqlalchemy import event

from .extensions import csrf, db, login_manager, migrate


def create_app(config_object: object | None = None) -> Flask:
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object or "config.Config")
    if not app.config.get("SECRET_KEY"):
        if os.environ.get("FLASK_ENV") == "production":
            raise RuntimeError("Set SECRET_KEY in the production environment.")
        app.config["SECRET_KEY"] = secrets.token_hex(32)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        def _enable_sqlite_foreign_keys(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        with app.app_context():
            event.listen(db.engine, "connect", _enable_sqlite_foreign_keys)

    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    from . import models  # noqa: F401
    from .auth import bp as auth_bp
    from .student import bp as student_bp
    from .admin import bp as admin_bp
    from .quizzes import bp as quizzes_bp
    from .cli import register_commands

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(quizzes_bp)
    app.register_blueprint(admin_bp)
    register_commands(app)

    @app.context_processor
    def inject_current_year():
        from .models import utcnow
        return {"current_year": utcnow().year}

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; script-src 'self' https://cdn.jsdelivr.net; img-src 'self' data:;")
        return response

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app
