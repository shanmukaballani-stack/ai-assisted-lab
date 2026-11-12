from app.extensions import db
from app.models import Category, Quiz, User
from conftest import login


def test_admin_access_control_and_quiz_question_management(client, users, app):
    login(client)
    assert client.get("/admin/").status_code == 403
    client.post("/logout")
    login(client, "admin@example.test", "safe-password-456")
    assert client.get("/admin/").status_code == 200
    response = client.post("/admin/categories", data={"name": "Math", "description": "Numbers"}, follow_redirects=True)
    assert b"Category created" in response.data
    with app.app_context():
        category = Category.query.filter_by(name="Math").one()
        category_id = category.id
    response = client.post("/admin/quizzes/new", data={
        "title": "Algebra", "description": "Practice", "category_id": category_id,
        "difficulty": "Intermediate", "time_limit_minutes": "20",
        "passing_percentage": "70", "max_attempts": "2", "show_feedback": "on",
    })
    quiz_id = int(response.headers["Location"].rsplit("/", 2)[-2])
    response = client.post(f"/admin/quizzes/{quiz_id}/questions", data={
        "prompt": "What is 2 + 2?", "option_1": "3", "option_2": "4",
        "option_3": "5", "option_4": "6", "correct_option": "2",
        "points": "2", "explanation": "Basic arithmetic.",
    }, follow_redirects=True)
    assert b"Question added" in response.data
    response = client.post(f"/admin/quizzes/{quiz_id}/edit", data={"action": "publish"}, follow_redirects=True)
    assert b"Quiz published" in response.data
    with app.app_context():
        quiz = db.session.get(Quiz, quiz_id)
        assert quiz.published is True
        assert len(quiz.questions) == 1
        assert sum(option.is_correct for option in quiz.questions[0].options) == 1


def test_admin_cannot_promote_or_deactivate_admin_or_self(client, users, app):
    login(client, "admin@example.test", "safe-password-456")
    response = client.post(f"/admin/users/{users['student']}/toggle", follow_redirects=True)
    assert b"Student account updated" in response.data
    response = client.post(f"/admin/users/{users['admin']}/toggle", follow_redirects=True)
    assert b"cannot deactivate your own administrator account" in response.data
    with app.app_context():
        assert db.session.get(User, users["admin"]).active
