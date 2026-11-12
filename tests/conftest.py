import pytest

from app import create_app
from app.extensions import db
from app.models import AnswerOption, Category, Question, Quiz, User


@pytest.fixture()
def app():
    app = create_app("config.TestConfig")
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def users(app):
    with app.app_context():
        student = User(name="Test Student", email="student@example.test", role="student")
        student.set_password("safe-password-123")
        admin = User(name="Test Admin", email="admin@example.test", role="admin")
        admin.set_password("safe-password-456")
        other = User(name="Other Student", email="other@example.test", role="student")
        other.set_password("safe-password-789")
        db.session.add_all([student, admin, other])
        db.session.commit()
        return {
            "student": student.id,
            "admin": admin.id,
            "other": other.id,
        }


@pytest.fixture()
def quiz(app):
    with app.app_context():
        category = Category(name="Python", description="Python concepts")
        quiz = Quiz(
            category=category,
            title="Python Basics",
            description="A test quiz",
            difficulty="Beginner",
            time_limit_seconds=300,
            passing_percentage=50,
            max_attempts=2,
            published=True,
            show_feedback=True,
        )
        for position, (prompt, options, correct) in enumerate([
            ("Which is immutable?", ["list", "tuple"], 2),
            ("What is 2 + 2?", ["3", "4"], 2),
        ]):
            question = Question(prompt=prompt, points=1, position=position, explanation="Test explanation")
            question.options = [
                AnswerOption(text=text, is_correct=index == correct, position=index - 1)
                for index, text in enumerate(options, start=1)
            ]
            quiz.questions.append(question)
        db.session.add(quiz)
        db.session.commit()
        return quiz.id


def login(client, email="student@example.test", password="safe-password-123"):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)
