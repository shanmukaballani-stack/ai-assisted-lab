from datetime import timedelta

from .extensions import db
from .models import AttemptAnswer, Quiz, QuizAttempt, utcnow


class AttemptError(ValueError):
    pass


def start_attempt(quiz: Quiz, user_id: int) -> QuizAttempt:
    if not quiz.published or quiz.archived:
        raise AttemptError("This quiz is not available.")
    now = utcnow()
    if quiz.available_from and now < quiz.available_from:
        raise AttemptError("This quiz is not available yet.")
    if quiz.available_until and now >= quiz.available_until:
        raise AttemptError("The availability window for this quiz has closed.")
    if not quiz.questions:
        raise AttemptError("This quiz does not have any questions yet.")
    active = QuizAttempt.query.filter_by(
        user_id=user_id, quiz_id=quiz.id, status="in_progress"
    ).first()
    if active:
        if active.ends_at > now:
            return active
        finish_attempt(active, timed_out=True)
    completed = QuizAttempt.query.filter_by(
        user_id=user_id, quiz_id=quiz.id, status="completed"
    ).count()
    if quiz.max_attempts is not None and completed >= quiz.max_attempts:
        raise AttemptError("You have reached the attempt limit for this quiz.")

    now = utcnow()
    attempt = QuizAttempt(
        user_id=user_id,
        quiz_id=quiz.id,
        quiz_title=quiz.title,
        passing_percentage=quiz.passing_percentage,
        time_limit_seconds=quiz.time_limit_seconds,
        show_feedback=quiz.show_feedback,
        started_at=now,
        ends_at=now + timedelta(seconds=quiz.time_limit_seconds),
        total_points=sum(question.points for question in quiz.questions),
    )
    db.session.add(attempt)
    db.session.flush()
    for position, question in enumerate(quiz.questions):
        correct_options = [option for option in question.options if option.is_correct]
        if len(question.options) < 2 or len(correct_options) != 1:
            raise AttemptError("This quiz has a question that is not configured correctly.")
        attempt.answers.append(
            AttemptAnswer(
                question_id=question.id,
                prompt_snapshot=question.prompt,
                options_snapshot=[
                    {"key": str(option.id), "text": option.text}
                    for option in question.options
                ],
                correct_option_key=str(correct_options[0].id),
                explanation_snapshot=question.explanation,
                points=question.points,
                position=position,
            )
        )
    db.session.commit()
    return attempt


def finish_attempt(attempt: QuizAttempt, timed_out: bool = False) -> QuizAttempt:
    if attempt.status == "completed":
        return attempt
    now = utcnow()
    if now > attempt.ends_at:
        timed_out = True
        now = attempt.ends_at
    score = 0
    for answer in attempt.answers:
        answer.is_correct = (
            answer.selected_option_key == answer.correct_option_key
            and answer.selected_option_key is not None
        )
        if answer.is_correct:
            score += answer.points
    percentage = (score / attempt.total_points * 100) if attempt.total_points else 0.0
    attempt.score_points = score
    attempt.percentage = round(percentage, 2)
    attempt.passed = percentage >= attempt.passing_percentage
    attempt.completed_at = now
    attempt.duration_seconds = min(
        attempt.time_limit_seconds,
        max(0, int((now - attempt.started_at).total_seconds())),
    )
    attempt.status = "completed"
    db.session.commit()
    return attempt
