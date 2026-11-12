from app.extensions import db
from app.models import User


def test_registration_hashes_password_and_rejects_duplicate(client, app):
    response = client.post(
        "/register",
        data={"name": "New Learner", "email": "new@example.test", "password": "a-long-password"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email="new@example.test").one()
        assert user.role == "student"
        assert user.password_hash != "a-long-password"
        assert user.check_password("a-long-password")
    client.post("/logout")
    duplicate = client.post(
        "/register",
        data={"name": "Again", "email": "new@example.test", "password": "a-long-password"},
        follow_redirects=True,
    )
    assert b"already exists" in duplicate.data
    with app.app_context():
        assert User.query.filter_by(email="new@example.test").count() == 1


def test_login_logout_and_account_lockout(client, users, app):
    for _ in range(6):
        response = client.post("/login", data={"email": "student@example.test", "password": "wrong"})
    assert b"Try again later" in response.data
    with app.app_context():
        user = db.session.get(User, users["student"])
        assert user.locked_until is not None
    client.post("/login", data={"email": "student@example.test", "password": "safe-password-123"})
    # A locked account cannot authenticate, even with the correct password.
    assert client.get("/dashboard").status_code == 302

    client.post("/login", data={"email": "admin@example.test", "password": "safe-password-456"})
    logout = client.post("/logout", follow_redirects=True)
    assert b"signed out" in logout.data
    assert client.get("/dashboard").status_code == 302


def test_reset_link_and_profile_password_change(client, users, app):
    from app.auth.routes import _reset_token

    with app.app_context():
        token = _reset_token(db.session.get(User, users["student"]))
    response = client.post(f"/reset-password/{token}", data={"password": "updated-password-456"}, follow_redirects=True)
    assert b"password has been changed" in response.data
    reused = client.post(f"/reset-password/{token}", data={"password": "another-password-789"}, follow_redirects=True)
    assert b"invalid or has expired" in reused.data
    with app.app_context():
        user = db.session.get(User, users["student"])
        assert user.check_password("updated-password-456")


def test_forgot_password_response_does_not_reveal_account(client):
    known = client.post("/forgot-password", data={"email": "student@example.test"}, follow_redirects=True)
    unknown = client.post("/forgot-password", data={"email": "missing@example.test"}, follow_redirects=True)
    assert b"If an active account matches" in known.data
    assert b"If an active account matches" in unknown.data
