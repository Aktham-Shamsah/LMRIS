# LRMIS Backend

FastAPI + PyMongo backend for the COMP4382 Land Registration Management Information System.

## Run Locally

```powershell
cd D:\pyML\lrmis\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Start MongoDB first, or use the root `docker-compose.yml`.

## Staff Access Stub

Staff-only endpoints use a simple role header:

```text
X-LRMIS-Role: staff
X-LRMIS-Role: surveyor
X-LRMIS-Role: registrar
```

No complex authentication is included; this matches the project requirement for a simple stub.

## OpenAPI

Run the API and open:

```text
http://localhost:8000/docs
http://localhost:8000/openapi.json
```

## Seed Data

```powershell
cd D:\pyML\lrmis\backend
python scripts\seed_demo_data.py
```

