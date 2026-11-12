from flask import Blueprint

bp = Blueprint("quizzes", __name__)

from . import routes  # noqa: E402,F401
