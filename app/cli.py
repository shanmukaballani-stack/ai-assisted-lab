import click
from flask import Flask
from werkzeug.security import generate_password_hash

from .extensions import db
from .models import AnswerOption, Category, Question, Quiz, User


def register_commands(app: Flask) -> None:
    @app.cli.command("create-admin")
    def create_admin() -> None:
        """Create the first administrator interactively; no credentials are stored in source."""
        from getpass import getpass

        email = click.prompt("Administrator email").strip().lower()
        name = click.prompt("Administrator name").strip()
        if not email or "@" not in email or len(email) > 254:
            raise click.ClickException("Enter a valid email address.")
        if not name or len(name) > 100:
            raise click.ClickException("Enter a name of 1 to 100 characters.")
        if User.query.filter_by(email=email).first():
            raise click.ClickException("An account already uses this email.")
        password = getpass("Administrator password (10+ characters): ")
        confirmation = getpass("Confirm password: ")
        if len(password) < 10 or password != confirmation:
            raise click.ClickException("Passwords must match and contain at least 10 characters.")
        user = User(name=name, email=email, role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Administrator {email} created.")

    @app.cli.command("seed-demo")
    def seed_demo() -> None:
        """Insert sample categories and quizzes without creating duplicate rows."""
        samples = [
            ("Python", "Programming fundamentals", "Python Essentials", "Practice core Python concepts.", "Beginner",
             [("Which value is immutable?", ["list", "dictionary", "tuple", "set"], 3, "Tuples cannot be changed after creation."),
              ("What does len([1, 2, 3]) return?", ["2", "3", "4", "None"], 2, "len returns the number of items.")]),
            ("Science", "Science and nature", "Everyday Science", "A short general science quiz.", "Beginner",
             [("Which planet is known as the Red Planet?", ["Venus", "Mars", "Jupiter", "Mercury"], 2, "Iron minerals give Mars its reddish appearance."),
              ("What is the chemical symbol for water?", ["CO2", "O2", "H2O", "NaCl"], 3, "A water molecule contains two hydrogen atoms and one oxygen atom.")]),
        ]
        for category_name, category_description, title, description, difficulty, questions in samples:
            category = Category.query.filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name, description=category_description)
                db.session.add(category)
                db.session.flush()
            quiz = Quiz.query.filter_by(title=title, category_id=category.id).first()
            if quiz:
                continue
            quiz = Quiz(
                category=category,
                title=title,
                description=description,
                difficulty=difficulty,
                time_limit_seconds=600,
                passing_percentage=60,
                published=True,
                show_feedback=True,
            )
            for position, (prompt, options, correct, explanation) in enumerate(questions):
                question = Question(prompt=prompt, explanation=explanation, points=1, position=position)
                question.options = [
                    AnswerOption(text=text, is_correct=index == correct, position=index - 1)
                    for index, text in enumerate(options, start=1)
                ]
                quiz.questions.append(question)
            db.session.add(quiz)
        db.session.commit()
        click.echo("Sample categories and quizzes are ready.")
