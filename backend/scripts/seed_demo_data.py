from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.indexes import create_indexes  # noqa: E402
from app.db.mongo import get_db  # noqa: E402


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def seed() -> None:
    db = get_db()
    create_indexes(db)

    applicants = [
        {
            "applicant_id": "APP-400000000",
            "full_name": "Nour Ahmad",
            "applicant_type": "citizen",
            "identity": {"national_id": "400000000", "verified": True, "verification_method": "otp_stub", "verified_at": dt("2026-01-20T08:20:00Z")},
            "contacts": {"email": "nour@example.com", "phone": "+970599000000"},
            "address": {"city": "Ramallah", "neighborhood": "Al Tireh", "zone_id": "ZONE-RM-01"},
            "verification_state": "verified",
            "preferences": {"preferred_contact": "email", "language": "ar", "notifications": {"on_status_change": True, "on_missing_documents": True, "on_certificate_ready": True}},
            "privacy_settings": {"share_contact_with_staff": True, "public_certificate_lookup": False},
            "linked_applications": ["LRMIS-2026-0001", "LRMIS-2026-0002"],
            "stats": {"total_applications": 2, "approved_applications": 1, "pending_applications": 1},
            "created_at": dt("2026-01-20T08:10:00Z"),
        },
        {
            "applicant_id": "APP-401111111",
            "full_name": "Rami Khalil Law Office",
            "applicant_type": "lawyer",
            "identity": {"national_id": "401111111", "verified": True, "verification_method": "registry_stub"},
            "contacts": {"email": "rami.law@example.com", "phone": "+970599222222"},
            "address": {"city": "Ramallah", "neighborhood": "Al Masyoun", "zone_id": "ZONE-RM-02"},
            "verification_state": "verified",
            "linked_applications": ["LRMIS-2026-0003"],
            "stats": {"total_applications": 1, "approved_applications": 0, "pending_applications": 1},
            "created_at": dt("2026-01-22T09:00:00Z"),
        },
    ]

    parcels = [
        {
            "parcel_code": "RM-Z01-B12-P145",
            "parcel_number": "145",
            "block_number": "12",
            "basin_number": "3",
            "zone_id": "ZONE-RM-01",
            "current_owner_refs": [{"applicant_id": "APP-400000000", "share": "1/1"}],
            "area_sqm": 850.5,
            "land_use": "residential",
            "registration_status": "registered",
            "geometry": {"type": "Polygon", "coordinates": [[[35.2001, 31.9021], [35.2015, 31.9021], [35.2015, 31.9030], [35.2001, 31.9030], [35.2001, 31.9021]]]},
            "address_hint": "Ramallah - Al Tireh",
            "dispute_state": "none",
            "created_at": dt("2026-01-10T08:00:00Z"),
            "updated_at": dt("2026-02-01T10:00:00Z"),
        },
        {
            "parcel_code": "RM-Z02-B08-P088",
            "parcel_number": "088",
            "block_number": "08",
            "basin_number": "4",
            "zone_id": "ZONE-RM-02",
            "current_owner_refs": [{"applicant_id": "APP-401111111", "share": "1/1"}],
            "area_sqm": 620.0,
            "land_use": "commercial",
            "registration_status": "pending_transfer",
            "geometry": {"type": "Polygon", "coordinates": [[[35.2050, 31.9060], [35.2062, 31.9060], [35.2062, 31.9071], [35.2050, 31.9071], [35.2050, 31.9060]]]},
            "address_hint": "Ramallah - Al Masyoun",
            "dispute_state": "under_objection",
            "created_at": dt("2026-01-11T08:00:00Z"),
            "updated_at": dt("2026-02-02T10:00:00Z"),
        },
    ]

    applications = [
        {
            "application_id": "LRMIS-2026-0001",
            "application_type": "ownership_transfer",
            "status": "approved",
            "priority": "normal",
            "applicant_ref": {"applicant_id": "APP-400000000", "applicant_type": "citizen", "submitted_by_representative": False},
            "parcel_ref": {"parcel_id": "RM-Z01-B12-P145", "parcel_code": "RM-Z01-B12-P145", "parcel_number": "145", "block_number": "12", "basin_number": "3", "zone_id": "ZONE-RM-01"},
            "description": "Ownership transfer application for parcel 145, block 12.",
            "tags": ["ownership_transfer", "requires_legal_review"],
            "workflow": {"current_state": "approved", "allowed_next": ["certificate_issued"], "transition_rules_version": "v1.0"},
            "required_documents": [
                {"document_type": "ownership_deed", "required": True, "status": "verified"},
                {"document_type": "id_copy", "required": True, "status": "verified"},
                {"document_type": "sale_contract", "required": True, "status": "verified"},
            ],
            "documents": [],
            "timestamps": {
                "submitted_at": dt("2026-02-01T09:00:00Z"),
                "pre_checked_at": dt("2026-02-01T10:00:00Z"),
                "survey_required_at": None,
                "surveyed_at": None,
                "legal_review_at": dt("2026-02-04T09:00:00Z"),
                "approved_at": dt("2026-02-05T12:00:00Z"),
                "certificate_issued_at": None,
                "closed_at": None,
                "updated_at": dt("2026-02-05T12:00:00Z"),
            },
            "assignment": {"assigned_surveyor_id": None, "assigned_registrar_id": "REG-RM-01", "assignment_policy": "zone+workload+availability"},
            "objection": {"has_objection": False, "objection_ids": []},
            "legal_review": {"completed": True, "decision": "approved", "notes": "Ownership chain verified."},
            "internal": {"notes": ["Initial pre-check completed."], "visibility": "staff_only"},
        },
        {
            "application_id": "LRMIS-2026-0002",
            "application_type": "boundary_correction",
            "status": "survey_required",
            "priority": "high",
            "applicant_ref": {"applicant_id": "APP-400000000", "applicant_type": "citizen", "submitted_by_representative": False},
            "parcel_ref": {"parcel_id": "RM-Z01-B12-P145", "parcel_code": "RM-Z01-B12-P145", "parcel_number": "145", "block_number": "12", "basin_number": "3", "zone_id": "ZONE-RM-01", "geometry": parcels[0]["geometry"]},
            "description": "Boundary correction request after neighbor complaint.",
            "tags": ["boundary_correction"],
            "workflow": {"current_state": "survey_required", "allowed_next": ["surveyed", "on_hold", "rejected"], "transition_rules_version": "v1.0"},
            "required_documents": [{"document_type": "ownership_deed", "required": True, "status": "uploaded"}],
            "timestamps": {"submitted_at": dt("2026-03-01T09:00:00Z"), "pre_checked_at": dt("2026-03-01T11:00:00Z"), "survey_required_at": dt("2026-03-02T09:00:00Z"), "surveyed_at": None, "legal_review_at": None, "approved_at": None, "certificate_issued_at": None, "closed_at": None, "updated_at": dt("2026-03-02T09:00:00Z")},
            "assignment": {"assigned_surveyor_id": None, "assigned_registrar_id": "REG-RM-01", "assignment_policy": None},
            "objection": {"has_objection": False, "objection_ids": []},
            "legal_review": {"completed": False, "decision": None, "notes": None},
            "internal": {"notes": [], "visibility": "staff_only"},
        },
        {
            "application_id": "LRMIS-2026-0003",
            "application_type": "parcel_subdivision",
            "status": "under_objection",
            "priority": "normal",
            "applicant_ref": {"applicant_id": "APP-401111111", "applicant_type": "lawyer", "submitted_by_representative": True},
            "parcel_ref": {"parcel_id": "RM-Z02-B08-P088", "parcel_code": "RM-Z02-B08-P088", "parcel_number": "088", "block_number": "08", "basin_number": "4", "zone_id": "ZONE-RM-02", "geometry": parcels[1]["geometry"]},
            "description": "Subdivision request with active objection.",
            "tags": ["parcel_subdivision", "disputed"],
            "workflow": {"current_state": "under_objection", "allowed_next": ["legal_review", "on_hold", "rejected"], "transition_rules_version": "v1.0"},
            "required_documents": [{"document_type": "ownership_deed", "required": True, "status": "verified"}],
            "timestamps": {"submitted_at": dt("2026-03-04T09:00:00Z"), "pre_checked_at": dt("2026-03-04T10:00:00Z"), "survey_required_at": dt("2026-03-05T09:00:00Z"), "surveyed_at": dt("2026-03-07T11:00:00Z"), "legal_review_at": dt("2026-03-08T11:00:00Z"), "approved_at": None, "certificate_issued_at": None, "closed_at": None, "updated_at": dt("2026-03-09T08:00:00Z")},
            "assignment": {"assigned_surveyor_id": "SURV-RM-04", "assigned_registrar_id": "REG-RM-01", "assignment_policy": "zone+workload+availability+skill+priority"},
            "objection": {"has_objection": True, "objection_ids": ["OBJ-2026-0001"]},
            "legal_review": {"completed": False, "decision": None, "notes": None},
            "internal": {"notes": ["Objection awaiting registrar decision."], "visibility": "staff_only"},
        },
    ]

    staff_members = [
        {
            "staff_id": "SURV-RM-04",
            "staff_code": "SURV-RM-04",
            "name": "Survey Team A",
            "role": "surveyor",
            "department": "Cadastral Survey",
            "skills": ["boundary_survey", "parcel_subdivision", "gps_mapping"],
            "coverage": {"zone_ids": ["ZONE-RM-01", "ZONE-RM-02"], "geo_fence": {"type": "Polygon", "coordinates": [[[35.19, 31.89], [35.22, 31.89], [35.22, 31.92], [35.19, 31.92], [35.19, 31.89]]]}},
            "schedule": {"timezone": "Asia/Jerusalem", "shifts": [{"day": "Mon", "start": "08:00", "end": "16:00"}], "on_call": False},
            "workload": {"active_tasks": 1, "max_tasks": 10},
            "contacts": {"phone": "+970599111111", "email": "survey_a@example.com"},
            "active": True,
            "created_at": dt("2026-01-10T09:00:00Z"),
        },
        {
            "staff_id": "REG-RM-01",
            "staff_code": "REG-RM-01",
            "name": "Registrar Office Ramallah",
            "role": "registrar",
            "department": "Land Registrar",
            "skills": ["legal_review", "ownership_verification"],
            "coverage": {"zone_ids": ["ZONE-RM-01", "ZONE-RM-02"]},
            "workload": {"active_tasks": 3, "max_tasks": 20},
            "contacts": {"phone": "+970599333333", "email": "registrar@example.com"},
            "active": True,
            "created_at": dt("2026-01-10T09:30:00Z"),
        },
    ]

    documents = [
        {"document_id": "DOC-1", "application_id": "LRMIS-2026-0001", "document_type": "ownership_deed", "filename": "ownership-deed.pdf", "status": "verified", "is_ownership_doc": True, "uploaded_at": dt("2026-02-01T09:05:00Z")},
        {"document_id": "DOC-2", "application_id": "LRMIS-2026-0002", "document_type": "ownership_deed", "filename": "boundary-deed.pdf", "status": "uploaded", "is_ownership_doc": True, "uploaded_at": dt("2026-03-01T09:05:00Z")},
    ]

    survey_tasks = [
        {"task_id": "SURV-2026-0001", "application_id": "LRMIS-2026-0003", "parcel_id": "RM-Z02-B08-P088", "assigned_surveyor_id": "SURV-RM-04", "status": "registrar_reviewed", "milestones": [{"type": "assigned", "at": dt("2026-03-05T10:00:00Z"), "by": "system", "meta": {"reason": "zone and workload match"}}, {"type": "registrar_reviewed", "at": dt("2026-03-08T10:00:00Z"), "by": "REG-RM-01", "meta": {"decision": "accept"}}], "field_notes": ["Neighbor boundary markers photographed."], "report_uploaded": True, "created_at": dt("2026-03-05T10:00:00Z"), "updated_at": dt("2026-03-08T10:00:00Z")},
    ]

    survey_reports = [
        {"report_id": "RPT-SURV-2026-0001", "application_id": "LRMIS-2026-0003", "report_title": "Subdivision field report", "surveyor_id": "SURV-RM-04", "findings": "Parcel boundaries match submitted sketch.", "evidence_files": [], "uploaded_at": dt("2026-03-07T11:00:00Z")},
    ]

    objections = [
        {"objection_id": "OBJ-2026-0001", "application_id": "LRMIS-2026-0003", "reason": "Neighbor claims access path is omitted.", "submitted_by": "APP-400000000", "status": "open", "evidence_documents": [], "submitted_at": dt("2026-03-09T08:00:00Z")},
    ]

    certificates = [
        {"certificate_id": "CERT-2026-0001", "application_id": "LRMIS-2026-0001", "parcel_id": "RM-Z01-B12-P145", "certificate_type": "ownership_certificate", "status": "issued", "issued_to": {"applicant_id": "APP-400000000", "full_name": "Nour Ahmad"}, "issued_at": dt("2026-02-10T12:00:00Z"), "issued_by": "REG-RM-01", "verification": {"qr_code_url": "/certificates/CERT-2026-0001/verify", "digital_signature_stub": "signed_hash_example"}},
    ]

    for collection_name, docs, key in [
        ("applicants", applicants, "applicant_id"),
        ("parcels", parcels, "parcel_code"),
        ("land_applications", applications, "application_id"),
        ("staff_members", staff_members, "staff_code"),
        ("application_documents", documents, "document_id"),
        ("survey_tasks", survey_tasks, "task_id"),
        ("survey_reports", survey_reports, "report_id"),
        ("objections", objections, "objection_id"),
        ("certificates", certificates, "certificate_id"),
    ]:
        for doc in docs:
            db[collection_name].update_one({key: doc[key]}, {"$set": doc}, upsert=True)

    for app in applications:
        db.performance_logs.update_one(
            {"application_id": app["application_id"]},
            {
                "$set": {
                    "application_id": app["application_id"],
                    "event_stream": [
                        {"type": "submitted", "by": {"actor_type": "applicant", "actor_id": app["applicant_ref"]["applicant_id"]}, "at": app["timestamps"]["submitted_at"], "meta": {"channel": "web"}},
                        {"type": app["status"], "by": {"actor_type": "system", "actor_id": "seed"}, "at": app["timestamps"]["updated_at"], "meta": {}},
                    ],
                    "computed_kpis": {"processing_days": None, "precheck_minutes": 60, "survey_delay_days": None, "certificate_issued": app["status"] == "certificate_issued"},
                }
            },
            upsert=True,
        )

    print("Seeded LRMIS demo data.")


if __name__ == "__main__":
    seed()

