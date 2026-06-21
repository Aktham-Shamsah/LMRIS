# Modular Pull Request Workflow

## Student A

Branch: `feature/applications-applicants-certificates`

Owns:

- Applications
- Applicants
- Certificates
- Audit timeline hooks used by these modules
- Applicant-facing React pages
- Application management/detail pages touched by application workflow

Checks:

- Endpoint names match the PDF.
- `POST /applications/` supports idempotency.
- Workflow guards reject invalid transitions.
- Objections move applications to `under_objection`.
- Certificates can only be issued from `approved`.

## Student B

Branch: `feature/staff-survey-registrar`

Owns:

- Staff
- Survey assignment
- Survey milestones
- Survey reports
- Registrar review
- Surveyor and registrar React pages

Checks:

- Assignment policy uses zone, availability, workload, skills, priority, and existing tasks.
- Milestones follow the exact order.
- Survey actions cannot bypass application workflow.
- Registrar decisions can move to `legal_review`, `approved`, `on_hold`, or `rejected` as allowed.

## Group

Branch: `feature/analytics-map`

Owns:

- Analytics endpoints
- GeoJSON feeds
- Leaflet live map
- Analytics dashboard

