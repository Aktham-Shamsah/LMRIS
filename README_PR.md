# Student B PR Notes - lrmis-surveyors-registrar-module-main

Branch to create:

```text
feature/staff-survey-registrar
```

## What Changed

- Cleaned the original Repo B ownership area by excluding committed caches and generated artifacts.
- Preserved and aligned the assignment policy from Repo B:
  - zone match
  - surveyor availability
  - workload balancing
  - skill match
  - priority
  - existing assigned tasks
- Refactored the module into:
  - `backend/app/modules/staff`
  - `backend/app/modules/survey`
  - `backend/app/modules/registrar`
  - `backend/app/modules/audit`
- Added a simple staff-only role header stub through `X-LRMIS-Role`.
- Updated frontend surveyor, registrar, and staff pages to call final endpoints.

## PDF Requirements Satisfied

- Staff creation and staff profile lookup.
- Automatic surveyor assignment.
- Exact survey milestone order:

```text
assigned -> visit_scheduled -> arrived_on_site -> survey_started -> survey_completed -> report_uploaded -> registrar_reviewed
```

- Survey report metadata registration.
- Registrar review decisions:
  - accept survey report toward legal review
  - approve legal review
  - request documents
  - hold
  - reject
  - continue after objection
- Survey actions cannot bypass the application workflow.
- Collections: `staff_members`, `survey_tasks`, `survey_reports`, `performance_logs`.

## PR Steps

1. Clone the shared `lrmis` repository.
2. Create the branch:

```powershell
git checkout -b feature/staff-survey-registrar
```

3. Copy this folder's `backend/app/modules/staff`, `survey`, `registrar`, and `audit` into the shared repo.
4. Copy the included surveyor, registrar, staff pages, and API files into the shared repo.
5. Keep `.env.example`; do not commit `.env`.
6. Run:

```powershell
cd backend
pip install -r requirements.txt
pytest
```

7. From `frontend`, run:

```powershell
npm install
npm run build
```

8. Open a pull request into `main` and mention assignment policy, milestone order, registrar decisions, and access-control stub.

