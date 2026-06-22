from __future__ import annotations

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.shared.files import generated_pdf_target


def generate_certificate_pdf(certificate: dict) -> tuple[str, int]:
    certificate_id = certificate["certificate_id"]
    relative_path, absolute_path = generated_pdf_target("certificates", certificate_id, certificate_id)
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.fontName = "Helvetica-Bold"
    normal = styles["BodyText"]
    detail = certificate.get("certificate_details", {})

    doc = SimpleDocTemplate(
        str(absolute_path),
        pagesize=A4,
        rightMargin=22 * mm,
        leftMargin=22 * mm,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
    )
    rows = [
        ("Certificate ID", certificate_id),
        ("Application ID", certificate.get("application_id", "")),
        ("Issued To", detail.get("owner_name") or certificate.get("issued_to", {}).get("applicant_id", "")),
        ("Applicant ID", certificate.get("issued_to", {}).get("applicant_id", "")),
        ("Certificate Type", certificate.get("certificate_type", "").replace("_", " ").title()),
        ("Parcel Code", detail.get("parcel_code", "")),
        ("Parcel Number", detail.get("parcel_number", "")),
        ("Block / Basin", f"{detail.get('block_number', '')} / {detail.get('basin_number', '')}"),
        ("Zone", detail.get("zone_id", "")),
        ("Application Type", detail.get("application_type", "").replace("_", " ").title()),
        ("Issued By", certificate.get("issued_by", "")),
        ("Issued At", _format_dt(certificate.get("issued_at"))),
        ("Verification", certificate.get("verification", {}).get("digital_signature_stub", "")),
    ]
    table = Table(rows, colWidths=[45 * mm, 105 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3f0")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#1d4f45")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#b8c8c2")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story = [
        Paragraph("Land Registration Certificate", title_style),
        Spacer(1, 8 * mm),
        Paragraph(
            "This certificate confirms that the referenced land registration application has completed the approved LRMIS workflow and certificate issuance checks.",
            normal,
        ),
        Spacer(1, 7 * mm),
        table,
        Spacer(1, 8 * mm),
        Paragraph(
            "Validation note: this PDF is generated from the official LRMIS certificate record. Verify the certificate ID and digital signature in the system before relying on printed copies.",
            normal,
        ),
    ]
    doc.build(story)
    return relative_path, absolute_path.stat().st_size


def _format_dt(value) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value or "")
