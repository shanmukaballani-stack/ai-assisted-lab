from flask import abort, current_app, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func

from ..models import Category, Quiz, QuizAttempt
from . import bp


@bp.get("/dashboard")
@login_required
def dashboard():
    completed = QuizAttempt.query.filter_by(user_id=current_user.id, status="completed")
    attempts = completed.order_by(QuizAttempt.completed_at.desc()).limit(6).all()
    total_completed = completed.count()
    average = completed.with_entities(func.avg(QuizAttempt.percentage)).scalar() or 0
    best = completed.with_entities(func.max(QuizAttempt.percentage)).scalar() or 0
    available = Quiz.query.filter_by(published=True, archived=False).count()
    trend_attempts = list(reversed(
        completed.order_by(QuizAttempt.completed_at.desc()).limit(20).all()
    ))
    trend = [{"label": item.completed_at.strftime("%b %d"), "score": item.percentage} for item in trend_attempts]
    category_totals: dict[str, list[float | int]] = {}
    for attempt in completed.all():
        category_name = attempt.quiz.category.name if attempt.quiz else "Archived"
        scores = category_totals.setdefault(category_name, [0.0, 0])
        scores[0] += attempt.percentage or 0
        scores[1] += 1
    categories = [
        {"name": name, "score": round(total / count, 1)}
        for name, (total, count) in category_totals.items()
    ]
    recommended = Quiz.query.filter_by(published=True, archived=False).order_by(Quiz.created_at.desc()).limit(3).all()
    return render_template(
        "dashboard/student.html",
        attempts=attempts,
        total_completed=total_completed,
        average=round(average, 1),
        best=round(best, 1),
        available=available,
        trend=trend,
        categories=categories,
        recommended=recommended,
    )


@bp.get("/history")
@login_required
def history():
    page = QuizAttempt.query.filter_by(user_id=current_user.id, status="completed").order_by(
        QuizAttempt.completed_at.desc()
    ).paginate(page=max(1, request.args.get("page", 1, type=int)), per_page=15, error_out=False)
    return render_template("dashboard/history.html", page=page)


@bp.get("/leaderboard")
@login_required
def leaderboard():
    if not current_app.config.get("LEADERBOARD_ENABLED"):
        abort(404)
    rows = QuizAttempt.query.filter_by(status="completed").order_by(
        QuizAttempt.percentage.desc(), QuizAttempt.duration_seconds.asc(), QuizAttempt.completed_at.asc()
    ).limit(50).all()
    # The board ranks individual attempts; equal percentages break by faster completion, then earlier submission.
    return render_template("dashboard/leaderboard.html", rows=rows)
