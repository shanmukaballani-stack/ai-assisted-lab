from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import AttemptAnswer, Category, Quiz, QuizAttempt, utcnow
from ..services import AttemptError, finish_attempt, start_attempt
from . import bp


@bp.get("/")
def landing():
    quizzes = Quiz.query.filter_by(published=True, archived=False).order_by(Quiz.created_at.desc()).limit(3).all()
    return render_template("landing.html", featured_quizzes=quizzes)


@bp.get("/quizzes")
@login_required
def catalogue():
    query = Quiz.query.filter_by(published=True, archived=False)
    term = request.args.get("q", "").strip()[:100]
    difficulty = request.args.get("difficulty", "")
    category_id = request.args.get("category", type=int)
    if term:
        query = query.filter(Quiz.title.ilike(f"%{term}%"))
    if difficulty in {"Beginner", "Intermediate", "Advanced"}:
        query = query.filter_by(difficulty=difficulty)
    if category_id:
        query = query.filter_by(category_id=category_id)
    page = query.order_by(Quiz.created_at.desc()).paginate(
        page=max(1, request.args.get("page", 1, type=int)), per_page=9, error_out=False
    )
    return render_template(
        "quizzes/catalogue.html",
        page=page,
        categories=Category.query.order_by(Category.name).all(),
        term=term,
        difficulty=difficulty,
        category_id=category_id,
    )


@bp.get("/quizzes/<int:quiz_id>")
@login_required
def detail(quiz_id: int):
    quiz = db.get_or_404(Quiz, quiz_id)
    if not quiz.published or quiz.archived:
        abort(404)
    completed = QuizAttempt.query.filter_by(
        user_id=current_user.id, quiz_id=quiz.id, status="completed"
    ).count()
    active = QuizAttempt.query.filter_by(
        user_id=current_user.id, quiz_id=quiz.id, status="in_progress"
    ).first()
    can_start = quiz.max_attempts is None or completed < quiz.max_attempts
    return render_template("quizzes/detail.html", quiz=quiz, completed=completed, active=active, can_start=can_start)


@bp.post("/quizzes/<int:quiz_id>/start")
@login_required
def start(quiz_id: int):
    quiz = db.get_or_404(Quiz, quiz_id)
    if not quiz.published or quiz.archived:
        abort(404)
    try:
        attempt = start_attempt(quiz, current_user.id)
    except AttemptError as error:
        flash(str(error), "error")
        return redirect(url_for("quizzes.detail", quiz_id=quiz.id))
    return redirect(url_for("quizzes.play", attempt_id=attempt.id))


def _owned_attempt(attempt_id: int) -> QuizAttempt:
    attempt = db.get_or_404(QuizAttempt, attempt_id)
    if attempt.user_id != current_user.id:
        abort(404)
    return attempt


@bp.get("/attempts/<int:attempt_id>")
@login_required
def play(attempt_id: int):
    attempt = _owned_attempt(attempt_id)
    if attempt.status == "completed":
        return redirect(url_for("quizzes.result", attempt_id=attempt.id))
    if utcnow() >= attempt.ends_at:
        finish_attempt(attempt, timed_out=True)
        flash("Time is up. Your answers have been submitted.", "info")
        return redirect(url_for("quizzes.result", attempt_id=attempt.id))
    remaining_seconds = max(0, int((attempt.ends_at - utcnow()).total_seconds()))
    answer_index = max(0, request.args.get("question", 1, type=int) - 1)
    answer_index = min(answer_index, len(attempt.answers) - 1)
    return render_template(
        "quizzes/player.html",
        attempt=attempt,
        answer=attempt.answers[answer_index],
        answer_index=answer_index,
        remaining_seconds=remaining_seconds,
    )


@bp.post("/attempts/<int:attempt_id>/answers/<int:answer_id>")
@login_required
def save_answer(attempt_id: int, answer_id: int):
    attempt = _owned_attempt(attempt_id)
    if attempt.status != "in_progress":
        return jsonify(error="This attempt has already been submitted."), 409
    if utcnow() >= attempt.ends_at:
        finish_attempt(attempt, timed_out=True)
        return jsonify(error="Time expired; the attempt was submitted."), 409
    answer = db.session.get(AttemptAnswer, answer_id)
    if not answer or answer.attempt_id != attempt.id:
        abort(404)
    selected = request.form.get("option_key", "")
    allowed = {option["key"] for option in answer.options_snapshot}
    if selected and selected not in allowed:
        return jsonify(error="That answer is not valid for this question."), 400
    answer.selected_option_key = selected or None
    db.session.commit()
    return jsonify(saved=True)


@bp.post("/attempts/<int:attempt_id>/submit")
@login_required
def submit(attempt_id: int):
    attempt = _owned_attempt(attempt_id)
    if attempt.status == "in_progress":
        finish_attempt(attempt, timed_out=utcnow() >= attempt.ends_at)
        flash("Your quiz has been submitted.", "success")
    return redirect(url_for("quizzes.result", attempt_id=attempt.id))


@bp.get("/attempts/<int:attempt_id>/result")
@login_required
def result(attempt_id: int):
    attempt = _owned_attempt(attempt_id)
    if attempt.status == "in_progress":
        return redirect(url_for("quizzes.play", attempt_id=attempt.id))
    correct_count = sum(answer.is_correct is True for answer in attempt.answers)
    return render_template("quizzes/result.html", attempt=attempt, correct_count=correct_count)


@bp.get("/attempts/<int:attempt_id>/review")
@login_required
def review(attempt_id: int):
    attempt = _owned_attempt(attempt_id)
    if attempt.status != "completed":
        return redirect(url_for("quizzes.play", attempt_id=attempt.id))
    if not attempt.show_feedback:
        flash("Answer review is not available for this quiz.", "info")
        return redirect(url_for("quizzes.result", attempt_id=attempt.id))
    return render_template("quizzes/review.html", attempt=attempt)
