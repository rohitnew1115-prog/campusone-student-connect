# CampusOne

**One Campus. Every Connection.** A mobile friendly campus platform built with HTML, CSS, vanilla JavaScript, Flask and SQLite.

The supplied presentation describes three initial services (Team Finder, Student Tutoring, Lost & Found) and excludes payments, official records, public access and identity verification. The accompanying master development prompt expands the requested scope to six modules. This implementation preserves those three core workflows and also provides opportunity, mentoring and campus issue workflows.

## Run locally

Requires Python 3.10 or later.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env: set a long random CAMPUSONE_SECRET and a campus-admin email.
$env:CAMPUSONE_SECRET = "your-long-random-secret"
$env:CAMPUSONE_ADMIN_EMAIL = "admin@your-campus.edu"
python app.py
```

Open http://127.0.0.1:5000. Register using the configured administrator email to create the first admin. Other signups are students. Data is stored in `instance/campusone.sqlite3`; uploaded images are stored in `instance/uploads/`. Keep both on persistent storage and back them up.

## Features

- Password hashed account registration, login, logout, profile editing and role checks.
- Team project posts, candidate skill and interest ranking, invitations and responses.
- Tutor profiles, subject filtering and session requests.
- Lost/found listings, private claims and status moderation.
- Admin published opportunities and student bookmarks.
- Mentor listings, requests and responses.
- Campus issue IDs, history, administrator status updates and student notifications.
- Dashboard counts, in-app notifications, searchable listings and validated private image uploads.
- Responsive desktop and mobile interface with PWA manifest, service worker and install metadata.

## Important scope notes

The platform uses a common SQLite records/requests schema for the six modules. It does not claim institutional identity verification: campus eligibility rules and email verification are not configured. Configure an institutional mail service before offering password reset; the current forgot-password flow does not send email. Notifications are in-app only. There is no deployed service URL or production database until a campus operator provisions hosting and a persistent disk. The Android project must be generated and signed with Android Studio/SDK before an APK can be distributed. The PWA install flow requires HTTPS in production.

The UI and API implement working create, search, request/response, status and notification flows, with focused integration tests. Advanced features from the prompt such as calendar sync, push notifications, tutor review moderation, formal mentor session scheduling, Windows native installer, production deployment, and a built APK require additional integrations or a provisioned environment.

## Production

Use a persistent disk mounted at `/data`, set `CAMPUSONE_DATA_DIR=/data`, set `CAMPUSONE_SECRET` to a generated secret, set `CAMPUSONE_ADMIN_EMAIL` before the first admin registers, and enable secure cookies behind HTTPS (`COOKIE_SECURE=1`). Run one Gunicorn worker for SQLite writes; use backups and monitor disk space. Configure TLS, reverse proxy request limits, SMTP, rate limiting and campus-approved CORS/origin policies before real campus use. `Dockerfile` is provided as a deployment starting point. Do not deploy SQLite on a temporary filesystem.

## Project layout

```text
app.py                   Flask API and SQLite schema/bootstrap
frontend/                HTML, CSS, vanilla JS, PWA metadata and icon
tests/                   Flask API integration tests
docs/                    API, data model, setup and deployment notes
Dockerfile               Production container starting point
capacitor.config.json    Capacitor Android packaging configuration
```

## Checks

Run `python -m unittest discover -s tests -v` for the backend workflow checks. See [the testing report](docs/TESTING_REPORT.md) for what was and was not exercised.
