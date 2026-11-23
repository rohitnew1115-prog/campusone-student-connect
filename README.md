# CampusOne

**One Campus. Every Connection.** A mobile friendly campus platform built with HTML, CSS, vanilla JavaScript, Flask and SQLite.

The app includes four campus modules: Team Finder, Student Tutoring, Lost & Found and Opportunity Board. It does not verify campus identity or replace official campus records.

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

To fill a local capstone demo with fictional examples, run `python database/seed_demo.py`. It adds 10 labelled demo student profiles, sample projects and teams, tutors, 12 opportunities and lost/found listings with original SVG item illustrations. It is safe to run more than once. Demo accounts have random, undisclosed password hashes and cannot sign in; use them as showcase content only.

## Features

- Password hashed account registration, login, logout, profile editing and role checks.
- Team project posts, candidate skill and interest ranking, invitations and responses.
- Tutor profiles, subject filtering and session requests.
- Lost/found listings, private claims and status moderation.
- Admin published opportunities and student bookmarks.
- Dashboard counts, in-app notifications, searchable listings and validated private image uploads.
- Responsive desktop and mobile interface with PWA manifest, service worker and install metadata.

## Important scope notes

The platform uses a common SQLite records/requests schema for the four modules. It does not claim institutional identity verification: campus eligibility rules and email verification are not configured. Configure an institutional mail service before offering password reset; the current forgot-password flow does not send email. Notifications are in-app only. Durable hosting requires a persistent volume for SQLite and uploaded files; `render-persistent.yaml` configures one, while `render.yaml` is the temporary free demo with ephemeral data. An Android project and signed APK are not included yet. PWA installation requires HTTPS in production.

The UI and API implement create, search, request/response, status and notification flows, with focused integration tests. Calendar sync, push notifications, tutor review moderation, email-based password recovery, a Windows native installer, production deployment and a built APK require additional integrations or a provisioned environment.

## Production

Use a persistent disk mounted at `/data`, set `CAMPUSONE_DATA_DIR=/data`, set `CAMPUSONE_SECRET` to a generated secret, set `CAMPUSONE_ADMIN_EMAIL` before the first admin registers, and enable secure cookies behind HTTPS (`COOKIE_SECURE=1`). Run one Gunicorn worker for SQLite writes; use backups and monitor disk space. Configure TLS, reverse proxy request limits, SMTP, rate limiting and campus-approved CORS/origin policies before real campus use. `Dockerfile` and `render.yaml` configure a production container, health check, HTTPS cookies, generated session secret and persistent `/data` storage for SQLite and uploads. Do not deploy SQLite on a temporary filesystem.

## Free phone demo

For a no-cost demo deployment, use the root `render.yaml` Blueprint in Render. It creates a public web service with a shareable HTTPS URL. The free service sleeps after 15 minutes without traffic and may take about a minute to wake up. Its filesystem is temporary, so accounts, listings, notifications and uploaded photos can disappear after restarts or redeploys. It is not suitable for durable student data. The persistent-disk configuration is in `render-persistent.yaml`.

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
