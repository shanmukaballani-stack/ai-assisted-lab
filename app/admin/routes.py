from functools import wraps
from datetime import datetime

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ..extensions import db
from ..models import AnswerOption, Category, Question, Quiz, QuizAttempt, User
from . import bp


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def _quiz_form(quiz: Quiz | None = None) -> dict:
    category_id = request.form.get("category_id", type=int)
    title = request.form.get("title", "").strip()
    difficulty = request.form.get("difficulty", "Beginner")
    try:
        minutes = int(request.form.get("time_limit_minutes", "15"))
        passing = float(request.form.get("passing_percentage", "60"))
        max_attempts_raw = request.form.get("max_attempts", "").strip()
        max_attempts = int(max_attempts_raw) if max_attempts_raw else None
    except ValueError:
        raise ValueError("Time limit, passing score, and attempt limit must be valid numbers.") from None
    category = db.session.get(Category, category_id) if category_id else None
    if not title or len(title) > 160:
        raise ValueError("Enter a quiz title of 1 to 160 characters.")
    if not category:
        raise ValueError("Select a valid category.")
    if difficulty not in {"Beginner", "Intermediate", "Advanced"}:
        raise ValueError("Select a valid difficulty.")
    if not 1 <= minutes <= 1440 or not 0 <= passing <= 100 or (max_attempts is not None and max_attempts < 1):
        raise ValueError("Check the time limit, passing percentage, and attempt limit.")
    try:
        available_from_raw = request.form.get("available_from", "").strip()
        available_until_raw = request.form.get("available_until", "").strip()
        available_from = datetime.fromisoformat(available_from_raw) if available_from_raw else None
        available_until = datetime.fromisoformat(available_until_raw) if available_until_raw else None
    except ValueError:
        raise ValueError("Availability dates must be valid date and time values.") from None
    if available_from and available_until and available_until <= available_from:
        raise ValueError("The end of the availability window must be after its start.")
    return {
        "category": category,
        "title": title,
        "description": request.form.get("description", "").strip()[:5000],
        "difficulty": difficulty,
        "time_limit_seconds": minutes * 60,
        "passing_percentage": passing,
        "max_attempts": max_attempts,
        "show_feedback": request.form.get("show_feedback") == "on",
        "available_from": available_from,
        "available_until": available_until,
    }


def _question_data() -> tuple[str, str, list[str], int, int]:
    prompt = request.form.get("prompt", "").strip()
    explanation = request.form.get("explanation", "").strip()
    options = [request.form.get(f"option_{index}", "").strip() for index in range(1, 5)]
    try:
        correct = int(request.form.get("correct_option", ""))
        points = int(request.form.get("points", "1"))
    except ValueError:
        raise ValueError("Choose a correct option and a valid positive point value.") from None
    if not prompt or len(prompt) > 2000 or not all(options) or any(len(option) > 500 for option in options):
        raise ValueError("Enter a question and four answer options (each up to 500 characters).")
    if correct not in range(1, 5) or points < 1 or points > 100:
        raise ValueError("Choose one of the four correct answers and set points from 1 to 100.")
    return prompt, explanation[:2000], options, correct, points


@bp.get("/")
@admin_required
def dashboard():
    users = User.query.count()
    quizzes = Quiz.query.filter_by(archived=False).count()
    published = Quiz.query.filter_by(archived=False, published=True).count()
    attempts = QuizAttempt.query.filter_by(status="completed")
    avg = attempts.with_entities(func.avg(QuizAttempt.percentage)).scalar() or 0
    recent = QuizAttempt.query.order_by(QuizAttempt.started_at.desc()).limit(8).all()
    return render_template(
        "admin/dashboard.html",
        users=users,
        quizzes=quizzes,
        published=published,
        attempts=attempts.count(),
        average=round(avg, 1),
        recent=recent,
    )


@bp.get("/quizzes")
@admin_required
def quizzes():
    page = Quiz.query.order_by(Quiz.updated_at.desc()).paginate(
        page=max(1, request.args.get("page", 1, type=int)), per_page=20, error_out=False
    )
    return render_template("admin/quizzes.html", page=page)


@bp.route("/quizzes/new", methods=["GET", "POST"])
@admin_required
def create_quiz():
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        try:
            fields = _quiz_form()
        except ValueError as error:
            flash(str(error), "error")
        else:
            quiz = Quiz(**fields)
            db.session.add(quiz)
            db.session.commit()
            flash("Quiz created. Add questions before publishing it.", "success")
            return redirect(url_for("admin.edit_quiz", quiz_id=quiz.id))
    return render_template("admin/quiz_form.html", quiz=None, categories=categories)


@bp.route("/quizzes/<int:quiz_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_quiz(quiz_id: int):
    quiz = db.get_or_404(Quiz, quiz_id)
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "save":
            try:
                fields = _quiz_form(quiz)
            except ValueError as error:
                flash(str(error), "error")
            else:
                for key, value in fields.items():
                    setattr(quiz, key, value)
                db.session.commit()
                flash("Quiz settings saved.", "success")
        elif action == "publish":
            if not quiz.questions:
                flash("Add at least one valid question before publishing.", "error")
            elif any(len(question.options) < 2 or sum(option.is_correct for option in question.options) != 1 for question in quiz.questions):
                flash("Every question needs at least two options and exactly one correct answer.", "error")
            else:
                quiz.published = True
                quiz.archived = False
                db.session.commit()
                flash("Quiz published.", "success")
        elif action == "unpublish":
            quiz.published = False
            db.session.commit()
            flash("Quiz unpublished.", "success")
        elif action == "archive":
            quiz.published = False
            quiz.archived = True
            db.session.commit()
            flash("Quiz archived. Historical attempts have been preserved.", "success")
        else:
            flash("Unsupported quiz action.", "error")
        return redirect(url_for("admin.edit_quiz", quiz_id=quiz.id))
    return render_template("admin/quiz_form.html", quiz=quiz, categories=categories)


@bp.post("/quizzes/<int:quiz_id>/questions")
@admin_required
def add_question(quiz_id: int):
    quiz = db.get_or_404(Quiz, quiz_id)
    try:
        prompt, explanation, options, correct, points = _question_data()
    except ValueError as error:
        flash(str(error), "error")
    else:
        question = Question(
            quiz=quiz,
            prompt=prompt,
            explanation=explanation,
            points=points,
            position=max((item.position for item in quiz.questions), default=-1) + 1,
        )
        for index, text in enumerate(options, start=1):
            question.options.append(
                AnswerOption(text=text, is_correct=index == correct, position=index - 1)
            )
        db.session.add(question)
        quiz.published = False
        db.session.commit()
        flash("Question added.", "success")
    return redirect(url_for("admin.edit_quiz", quiz_id=quiz.id))


@bp.route("/questions/<int:question_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_question(question_id: int):
    question = db.get_or_404(Question, question_id)
    if request.method == "POST":
        try:
            prompt, explanation, options, correct, points = _question_data()
        except ValueError as error:
            flash(str(error), "error")
        else:
            question.prompt = prompt
            question.explanation = explanation
            question.points = points
            for option in question.options:
                db.session.delete(option)
            db.session.flush()
            question.options = [
                AnswerOption(text=text, is_correct=index == correct, position=index - 1)
                for index, text in enumerate(options, start=1)
            ]
            question.quiz.published = False
            db.session.commit()
            flash("Question updated. Existing attempts retain their original question snapshot.", "success")
            return redirect(url_for("admin.edit_quiz", quiz_id=question.quiz_id))
    return render_template("admin/question_form.html", question=question, quiz=question.quiz)


@bp.post("/questions/<int:question_id>/delete")
@admin_required
def delete_question(question_id: int):
    question = db.get_or_404(Question, question_id)
    quiz_id = question.quiz_id
    question.quiz.published = False
    db.session.delete(question)
    db.session.commit()
    flash("Question removed. Historical attempt snapshots were preserved.", "success")
    return redirect(url_for("admin.edit_quiz", quiz_id=quiz_id))


@bp.get("/categories")
@admin_required
def categories():
    return render_template("admin/categories.html", categories=Category.query.order_by(Category.name).all())


@bp.post("/categories")
@admin_required
def create_category():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()[:300]
    if not name or len(name) > 80:
        flash("Category names must be 1 to 80 characters.", "error")
    elif Category.query.filter(func.lower(Category.name) == name.lower()).first():
        flash("That category already exists.", "error")
    else:
        db.session.add(Category(name=name, description=description))
        db.session.commit()
        flash("Category created.", "success")
    return redirect(url_for("admin.categories"))


@bp.post("/categories/<int:category_id>/delete")
@admin_required
def delete_category(category_id: int):
    category = db.get_or_404(Category, category_id)
    if category.quizzes:
        flash("A category used by quizzes cannot be deleted.", "error")
    else:
        db.session.delete(category)
        db.session.commit()
        flash("Category deleted.", "success")
    return redirect(url_for("admin.categories"))


@bp.get("/users")
@admin_required
def users():
    page = User.query.order_by(User.created_at.desc()).paginate(
        page=max(1, request.args.get("page", 1, type=int)), per_page=25, error_out=False
    )
    return render_template("admin/users.html", page=page)


@bp.post("/users/<int:user_id>/toggle")
@admin_required
def toggle_user(user_id: int):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own administrator account.", "error")
    elif user.is_admin:
        flash("Administrator status cannot be changed here.", "error")
    else:
        user.active = not user.active
        db.session.commit()
        flash("Student account updated.", "success")
    return redirect(url_for("admin.users"))


@bp.get("/reports")
@admin_required
def reports():
    page = QuizAttempt.query.filter_by(status="completed").order_by(
        QuizAttempt.completed_at.desc()
    ).paginate(page=max(1, request.args.get("page", 1, type=int)), per_page=25, error_out=False)
    return render_template("admin/reports.html", page=page)
