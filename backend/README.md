# LRMIS Backend

FastAPI + PyMongo backend for the COMP4382 Land Registration Management Information System.

## Run Locally

```powershell
cd ...\lrmis\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Start MongoDB first, or use the root `docker-compose.yml`.

## Demo Authentication

Seed data creates demo users for applicant, surveyor, registrar, supervisor, and admin roles.
Login with `POST /auth/login`, then send `Authorization: Bearer <token>`.

The implementation is intentionally small for a university demo: seed-only users, PBKDF2 password hashes, JWT access tokens, and role-based route dependencies.

## Notifications

Application workflow changes create notification events and email message records in MongoDB. SMTP delivery is disabled unless `EMAIL_ENABLED=true`.

Use `MAIL_FROM`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, and `REPLY_TO` in `.env` for real delivery. Keep `.env` private; only `.env.example` should be committed.

## OpenAPI

Run the API and open:

```text
http://localhost:8000/docs
http://localhost:8000/openapi.json
```

## Seed Data

```powershell
cd ...\lrmis\backend
python scripts\seed_demo_data.py
```

