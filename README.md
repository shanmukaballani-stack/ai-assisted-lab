# QuizMaster

QuizMaster is a Flask application for creating, taking, and reviewing quizzes. The existing standalone Student Expense Tracker files in this folder are retained; the Flask app starts from `run.py`.

## Requirements

- Python 3.12 or newer (the implementation was checked with Python 3.14.3)
- pip
- A current browser
- SQLite for local development (included with standard Python builds)

## Windows setup (PowerShell)

From this directory:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `SECRET_KEY` in `.env` to a long random value. For example, create one with:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated value into `.env`; do not commit `.env`. The app generates a temporary random key only for local development if no key is configured, which invalidates sessions when the process restarts. Production startup requires `SECRET_KEY`.

## Database setup and migrations

The initial schema migration is included. Set `FLASK_APP` and apply it:

```powershell
$env:FLASK_APP = "run.py"
flask db upgrade
```

When the models change later, generate and review a migration before applying it:

```powershell
flask db migrate -m "Describe the schema change"
flask db upgrade
```

Only run `flask db init` when creating a new project without the included `migrations` directory.

The default local database is created in `instance\quizmaster.sqlite`. Set `DATABASE_URL` to use another SQLAlchemy-supported database URL. SQLite connections enable foreign-key enforcement.

## Initial administrator and sample content

Create an administrator interactively. The CLI prompts for credentials and never uses a built-in account or password:

```powershell
flask create-admin
```

Add sample categories and published quizzes (safe to run again):

```powershell
flask seed-demo
```

No student or demo login account is created by seeding. New users can register at `/register`.

## Run the application

```powershell
$env:FLASK_APP = "run.py"
flask run
```

Visit `http://127.0.0.1:5000`. For HTTPS deployments, set `SESSION_COOKIE_SECURE=true`, configure a production `SECRET_KEY`, and terminate TLS at a trusted reverse proxy. Do not expose Flask's development server publicly; deploy using a production WSGI server and disable debug mode. Configure `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS`, and `MAIL_DEFAULT_SENDER` to deliver one-hour password reset links. Without SMTP configuration, recovery requests remain generic and no email is delivered.

## Tests

Tests use a separate in-memory SQLite database and disable CSRF only in the test configuration:

```powershell
python -m pytest
```

## Features and routes

### Public and account

- `/` landing page
- `/register`, `/login`, `/logout`
- `/forgot-password`, `/reset-password/<token>`
- `/profile` profile and password settings

### Student

- `/dashboard` live database metrics and learning trends
- `/quizzes` searchable catalogue with category/difficulty filters and pagination
- `/quizzes/<id>` details and attempt availability
- `/attempts/<id>` quiz player with countdown and answer autosave
- `/attempts/<id>/result`, `/attempts/<id>/review`
- `/history` private attempt history
- `/leaderboard` optional public display-name ranking (toggle `LEADERBOARD_ENABLED`)

### Administrator

- `/admin/` platform metrics
- `/admin/quizzes`, quiz create/edit/publish/unpublish/archive, question create/edit/remove
- `/admin/categories`, `/admin/users`, `/admin/reports`

Administrative endpoints require an authenticated administrator account. Registration always creates a student. Admin creation is a command-line operation; the user-management interface cannot promote accounts. Attempts keep question text, option text, answer correctness, feedback, and scoring thresholds as snapshots, so quiz edits and archival do not rewrite old results. Quiz records are archived rather than physically deleted.

## Architecture and security notes

- `app/__init__.py` provides the application factory; independent blueprints organize auth, student, quiz, and admin routes.
- SQLAlchemy models and relationships live in `app/models.py`; attempt creation and scoring are in `app/services.py`.
- Flask-Login protects authenticated views. Flask-WTF CSRF protection applies to POST requests. Passwords are Werkzeug-hashed, safe redirects are same-host checked, and repeated failed logins trigger a temporary account lock.
- The server validates quiz ownership, attempt state, option membership, time limits, attempt limits, and score calculation. The browser never receives correct-answer keys before submission.
- Inputs are bounded and validated on the server. Templates use Jinja autoescaping and all database access uses SQLAlchemy.
- Session cookies are HTTP-only and SameSite=Lax. Secure cookies can be enabled for HTTPS. Basic response security headers are configured in the app factory.
- Password-reset links are signed, expire after one hour, and are sent only when SMTP settings are configured. The forgot-password response does not disclose whether an account exists.
- Chart.js and Bootstrap are loaded from jsDelivr; the app requires network access for these CDN assets. Core server functionality does not depend on them.
- All availability date/time inputs are interpreted as UTC.

## Troubleshooting

- **`flask` cannot find the app:** activate the virtual environment and set `$env:FLASK_APP = "run.py"` from this directory.
- **Missing tables:** run `flask db upgrade` after installing dependencies and setting `FLASK_APP`.
- **Password reset email is not received:** verify SMTP host, port, credentials, sender, and TLS settings in `.env`; recovery responses intentionally remain generic.
- **A quiz cannot be published:** add at least one question with four options and exactly one correct answer.
- **A learner cannot start a quiz:** confirm it is published, not archived, within its availability window, and under its attempt limit.
- **Development sign-in expires after restarting:** configure a persistent `SECRET_KEY` in `.env`.

## Deployment

Set `FLASK_ENV=production`, a strong random `SECRET_KEY`, a persistent `DATABASE_URL`, `SESSION_COOKIE_SECURE=true`, and SMTP settings in the deployment environment. Apply reviewed migrations during release. Use HTTPS, a production WSGI server, a least-privilege database account, backups, and platform-level request throttling in front of the app. Do not place secrets or database files in source control.
