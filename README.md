# LRMIS

COMP4382 Land Registration Management Information System.

This repository is aligned with the project PDF requirements and uses:

- Backend: FastAPI, PyMongo, MongoDB, Pydantic, Uvicorn
- Frontend: React + Vite
- Map: OpenStreetMap + Leaflet
- Database: MongoDB

## Required Workflow

Main workflow:

```text
submitted -> pre_checked -> survey_required -> surveyed -> legal_review -> approved -> certificate_issued -> closed
```

Alternative states:

```text
rejected, on_hold, missing_documents, under_objection
```

Survey milestones:

```text
assigned -> visit_scheduled -> arrived_on_site -> survey_started -> survey_completed -> report_uploaded -> registrar_reviewed
```

## Run With Docker

```powershell
cd D:\pyML\lrmis
docker compose up --build
```

Then open:

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Seed demo data:

```powershell
docker compose exec backend python scripts/seed_demo_data.py
```

## Run Backend Locally

```powershell
cd D:\pyML\lrmis\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

## Run Frontend Locally

```powershell
cd D:\pyML\lrmis\frontend
npm install
npm run dev
```

## Sample Staff Header

Staff-only endpoints use a simple role header:

```text
X-LRMIS-Role: staff
X-LRMIS-Role: surveyor
X-LRMIS-Role: registrar
```

## Main Endpoints

Applications and applicant portal:

- `POST /applications/`
- `GET /applications/`
- `GET /applications/{application_id}`
- `PATCH /applications/{application_id}/transition`
- `POST /applications/{application_id}/hold`
- `POST /applications/{application_id}/reject`
- `POST /applications/{application_id}/certificate`
- `POST /applicants/`
- `GET /applicants/{applicant_id}`
- `GET /applicants/{applicant_id}/applications`
- `POST /applications/{application_id}/documents`
- `POST /applications/{application_id}/comments`
- `POST /applications/{application_id}/objections`
- `GET /applications/{application_id}/timeline`

Survey and registrar:

- `POST /staff/`
- `GET /staff/{staff_id}`
- `POST /applications/{application_id}/auto-assign-surveyor`
- `PATCH /applications/{application_id}/survey-milestone`
- `POST /applications/{application_id}/survey-report`
- `PATCH /applications/{application_id}/registrar-review`

Analytics and map:

- `GET /analytics/kpis`
- `GET /analytics/applications-by-status`
- `GET /analytics/applications-by-zone`
- `GET /analytics/processing-time`
- `GET /analytics/surveyors`
- `GET /analytics/registrars`
- `GET /analytics/geofeeds/parcels`
- `GET /analytics/geofeeds/pending-heatmap`

## MongoDB Collections

- `land_applications`
- `parcels`
- `applicants`
- `application_documents`
- `objections`
- `staff_members`
- `survey_tasks`
- `survey_reports`
- `certificates`
- `performance_logs`

Indexes are created automatically at FastAPI startup from `backend/app/db/indexes.py`.

## Demo IDs

After seeding:

- Applicant: `APP-400000000`
- Application: `LRMIS-2026-0001`
- Surveyor: `SURV-RM-04`
- Registrar: `REG-RM-01`
- Certificate: `CERT-2026-0001`
- Parcel: `RM-Z01-B12-P145`

## Module Ownership

- Student A branch: `feature/applications-applicants-certificates`
  - `backend/app/modules/applications`
  - `backend/app/modules/applicants`
  - `backend/app/modules/certificates`
  - `backend/app/modules/audit`
  - `frontend/src/pages/applicant`
  - related staff/registrar application pages

- Student B branch: `feature/staff-survey-registrar`
  - `backend/app/modules/staff`
  - `backend/app/modules/survey`
  - `backend/app/modules/registrar`
  - `backend/app/modules/audit`
  - `frontend/src/pages/surveyor`
  - related staff/registrar pages

- Group branch: `feature/analytics-map`
  - `backend/app/modules/analytics`
  - `frontend/src/pages/analytics`
  - `frontend/src/pages/map`

## PR Workflow

1. Create the branch named for your module.
2. Copy or merge only your owned module folders and pages.
3. Run backend tests from `backend`.
4. Run frontend build from `frontend`.
5. Open a PR into the shared `main` branch.
6. In the PR description, list the PDF endpoints and workflow rules you implemented.

## Tests

```powershell
cd D:\pyML\lrmis\backend
pytest
```

The tests cover applicant creation, idempotency, document metadata, workflow guards, survey assignment, survey milestones, registrar review, certificate guard behavior, and analytics responses.

