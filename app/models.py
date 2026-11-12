from __future__ import annotations

from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    active = db.Column(db.Boolean, nullable=False, default=True)
    failed_logins = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime)
    reset_generation = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    attempts = db.relationship("QuizAttempt", back_populates="user", lazy="select")

    __table_args__ = (
        CheckConstraint("role IN ('student', 'admin')", name="valid_role"),
        CheckConstraint("failed_logins >= 0", name="nonnegative_failed_logins"),
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    if not user_id.isdigit():
        return None
    user = db.session.get(User, int(user_id))
    return user if user and user.active else None


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    description = db.Column(db.String(300), nullable=False, default="")
    quizzes = db.relationship("Quiz", back_populates="category", lazy="select")


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id", ondelete="RESTRICT"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    difficulty = db.Column(db.String(20), nullable=False, default="Beginner")
    time_limit_seconds = db.Column(db.Integer, nullable=False, default=900)
    passing_percentage = db.Column(db.Float, nullable=False, default=60)
    max_attempts = db.Column(db.Integer)
    available_from = db.Column(db.DateTime)
    available_until = db.Column(db.DateTime)
    published = db.Column(db.Boolean, nullable=False, default=False, index=True)
    archived = db.Column(db.Boolean, nullable=False, default=False, index=True)
    show_feedback = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)
    category = db.relationship("Category", back_populates="quizzes")
    questions = db.relationship("Question", back_populates="quiz", cascade="all, delete-orphan", order_by="Question.position")
    attempts = db.relationship("QuizAttempt", back_populates="quiz")

    __table_args__ = (
        CheckConstraint("difficulty IN ('Beginner', 'Intermediate', 'Advanced')", name="valid_difficulty"),
        CheckConstraint("time_limit_seconds BETWEEN 60 AND 86400", name="valid_time_limit"),
        CheckConstraint("passing_percentage BETWEEN 0 AND 100", name="valid_passing_percentage"),
        CheckConstraint("max_attempts IS NULL OR max_attempts > 0", name="valid_attempt_limit"),
        Index("ix_quiz_catalogue", "published", "archived", "category_id"),
    )


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=False, default="")
    points = db.Column(db.Integer, nullable=False, default=1)
    position = db.Column(db.Integer, nullable=False, default=0)
    quiz = db.relationship("Quiz", back_populates="questions")
    options = db.relationship("AnswerOption", back_populates="question", cascade="all, delete-orphan", order_by="AnswerOption.position")
    __table_args__ = (
        CheckConstraint("points > 0", name="positive_question_points"),
        UniqueConstraint("quiz_id", "position", name="uq_question_position"),
    )


class AnswerOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id", ondelete="CASCADE"), nullable=False, index=True)
    text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    position = db.Column(db.Integer, nullable=False, default=0)
    question = db.relationship("Question", back_populates="options")
    __table_args__ = (UniqueConstraint("question_id", "position", name="uq_option_position"),)


class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False, index=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id", ondelete="RESTRICT"), nullable=False, index=True)
    quiz_title = db.Column(db.String(160), nullable=False)
    passing_percentage = db.Column(db.Float, nullable=False)
    time_limit_seconds = db.Column(db.Integer, nullable=False)
    show_feedback = db.Column(db.Boolean, nullable=False)
    started_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    ends_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Integer)
    score_points = db.Column(db.Integer)
    total_points = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float)
    passed = db.Column(db.Boolean)
    status = db.Column(db.String(20), nullable=False, default="in_progress", index=True)
    user = db.relationship("User", back_populates="attempts")
    quiz = db.relationship("Quiz", back_populates="attempts")
    answers = db.relationship("AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan", order_by="AttemptAnswer.position")
    __table_args__ = (
        CheckConstraint("status IN ('in_progress', 'completed')", name="valid_attempt_status"),
        CheckConstraint("total_points >= 0", name="nonnegative_total_points"),
        Index("ix_attempt_user_quiz_status", "user_id", "quiz_id", "status"),
    )


class AttemptAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("quiz_attempt.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id", ondelete="SET NULL"))
    prompt_snapshot = db.Column(db.Text, nullable=False)
    options_snapshot = db.Column(db.JSON, nullable=False)
    correct_option_key = db.Column(db.String(30), nullable=False)
    selected_option_key = db.Column(db.String(30))
    explanation_snapshot = db.Column(db.Text, nullable=False, default="")
    points = db.Column(db.Integer, nullable=False)
    position = db.Column(db.Integer, nullable=False)
    is_correct = db.Column(db.Boolean)
    attempt = db.relationship("QuizAttempt", back_populates="answers")
    __table_args__ = (UniqueConstraint("attempt_id", "position", name="uq_attempt_question_position"),)
