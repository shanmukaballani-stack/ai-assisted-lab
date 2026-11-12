from datetime import timedelta

from app.extensions import db
from app.models import AttemptAnswer, Quiz, QuizAttempt, User, utcnow
from conftest import login


def start(client, quiz_id):
    response = client.post(f"/quizzes/{quiz_id}/start")
    assert response.status_code == 302
    return int(response.headers["Location"].rsplit("/", 1)[-1])


def test_full_attempt_scores_only_server_side_and_duplicate_submit_is_safe(client, users, quiz, app):
    login(client)
    attempt_id = start(client, quiz)
    with app.app_context():
        attempt = db.session.get(QuizAttempt, attempt_id)
        answer_ids = [answer.id for answer in attempt.answers]
        keys = [answer.options_snapshot[1]["key"] for answer in attempt.answers]
        correct_keys = [answer.correct_option_key for answer in attempt.answers]
        assert keys == correct_keys
    player = client.get(f"/attempts/{attempt_id}")
    assert player.status_code == 200
    assert b"correct_option_key" not in player.data

    client.post(f"/attempts/{attempt_id}/answers/{answer_ids[0]}", data={"option_key": keys[0]})
    client.post(f"/attempts/{attempt_id}/answers/{answer_ids[1]}", data={"option_key": "invalid"})
    client.post(f"/attempts/{attempt_id}/submit", data={"score": 100})
    with app.app_context():
        attempt = db.session.get(QuizAttempt, attempt_id)
        assert attempt.status == "completed"
        assert attempt.score_points == 1
        assert attempt.total_points == 2
        assert attempt.percentage == 50
        assert attempt.passed is True
        completed_at = attempt.completed_at
    client.post(f"/attempts/{attempt_id}/submit", data={"score": 999})
    with app.app_context():
        attempt = db.session.get(QuizAttempt, attempt_id)
        assert attempt.score_points == 1
        assert attempt.completed_at == completed_at


def test_attempts_are_private_and_invalid_answers_are_rejected(client, users, quiz, app):
    login(client)
    attempt_id = start(client, quiz)
    with app.app_context():
        answer_id = db.session.get(QuizAttempt, attempt_id).answers[0].id
    invalid = client.post(f"/attempts/{attempt_id}/answers/{answer_id}", data={"option_key": "not-an-option"})
    assert invalid.status_code == 400
    client.post("/logout")
    login(client, "other@example.test", "safe-password-789")
    assert client.get(f"/attempts/{attempt_id}").status_code == 404
    assert client.get(f"/attempts/{attempt_id}/result").status_code == 404


def test_expired_attempt_is_scored_and_attempt_limit_enforced(client, users, quiz, app):
    login(client)
    attempt_id = start(client, quiz)
    with app.app_context():
        attempt = db.session.get(QuizAttempt, attempt_id)
        attempt.started_at = utcnow() - timedelta(seconds=302)
        attempt.ends_at = utcnow() - timedelta(seconds=2)
        attempt.answers[0].selected_option_key = attempt.answers[0].correct_option_key
        db.session.commit()
    response = client.get(f"/attempts/{attempt_id}")
    assert response.status_code == 302
    with app.app_context():
        expired = db.session.get(QuizAttempt, attempt_id)
        assert expired.status == "completed"
        assert expired.duration_seconds == expired.time_limit_seconds

    # Finish the remaining allowed attempt, then a new attempt is rejected.
    attempt2 = start(client, quiz)
    client.post(f"/attempts/{attempt2}/submit")
    third = client.post(f"/quizzes/{quiz}/start", follow_redirects=True)
    assert b"attempt limit" in third.data


def test_unpublished_quizzes_are_hidden_and_dashboard_and_history_are_user_scoped(client, users, quiz, app):
    login(client)
    attempt_id = start(client, quiz)
    client.post(f"/attempts/{attempt_id}/submit")
    assert client.get("/dashboard").status_code == 200
    assert b"Python Basics" in client.get("/history").data

    client.post("/logout")
    login(client, "other@example.test", "safe-password-789")
    assert b"Python Basics" not in client.get("/history").data

    with app.app_context():
        db.session.get(Quiz, quiz).published = False
        db.session.commit()
    assert client.get(f"/quizzes/{quiz}").status_code == 404
    assert client.post(f"/quizzes/{quiz}/start").status_code == 404


def test_attempt_start_snapshots_content_and_validates_question_membership(client, users, quiz, app):
    login(client)
    attempt_id = start(client, quiz)
    with app.app_context():
        attempt = db.session.get(QuizAttempt, attempt_id)
        answer_id = attempt.answers[0].id
        answer = db.session.get(AttemptAnswer, answer_id)
        prompt = answer.prompt_snapshot
        quiz_row = db.session.get(Quiz, quiz)
        quiz_row.questions[0].prompt = "Changed after start"
        db.session.commit()
        assert answer.prompt_snapshot == prompt
    assert client.post(f"/attempts/{attempt_id}/answers/999999", data={"option_key": "1"}).status_code == 404
