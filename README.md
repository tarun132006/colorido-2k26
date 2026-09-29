# COLORIDO 2K26

A FastAPI + SQLite event registration website for the COLORIDO 2K26 cultural and sports festival.

## Features

- Responsive public festival website
- Cultural and sports event catalogue with filters
- Event details, rules, schedules and registration
- Team registration with gender and team-size validation
- Registration confirmation pass and registration lookup
- Contact form backed by SQLite
- Announcements and sponsor sections
- Admin login API, registration listing/export, messages and result publishing
- Idempotent database seeding for fresh installations

## Run locally

Use Python 3.10+ (3.13 recommended).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:8000/`.

For a fresh database, the demo admin is:

- Username: `admin`
- Password: `colorido@2026`

Set `ADMIN_PASSWORD` before the first run if you want a different password. Do not use the demo password in a production deployment.

## API

- `GET /api/ping` — health check
- `GET /api/events` — event catalogue
- `GET /api/events/{slug}` — event details
- `POST /api/register` — create registration
- `GET /api/lookup` — find registration
- `POST /api/contact` — send contact message
- `POST /api/admin/login` — admin authentication
- `GET /api/admin/registrations` — protected registration list
- `GET /api/admin/export.csv` — protected CSV export
- `GET /api/admin/messages` — protected contact messages
- `POST /api/admin/announcements` — protected announcement publishing
- `POST /api/admin/results` — protected result publishing

The SQLite database is `colorido.db`.
