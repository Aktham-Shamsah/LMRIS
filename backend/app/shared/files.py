from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings

PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
_CHUNK_SIZE = 1024 * 1024


def upload_root() -> Path:
    settings = get_settings()
    root = Path(settings.upload_dir)
    if not root.is_absolute():
        root = Path.cwd() / root
    root.mkdir(parents=True, exist_ok=True)
    return root


def validate_pdf_upload(file: UploadFile) -> None:
    extension = Path(file.filename or "").suffix.lower()
    if extension != ".pdf":
        raise ValueError("Only PDF files are accepted for documents and evidence.")
    if file.content_type and file.content_type not in PDF_CONTENT_TYPES:
        raise ValueError("Only application/pdf uploads are accepted.")


def save_pdf_upload(category: str, owner_id: str, file: UploadFile, file_id: str | None = None) -> tuple[str, int]:
    validate_pdf_upload(file)
    safe_file_id = file_id or uuid4().hex
    relative_path = Path(category) / owner_id / f"{safe_file_id}.pdf"
    absolute_path = upload_root() / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    max_bytes = get_settings().max_upload_size_mb * 1024 * 1024
    size = 0
    try:
        with absolute_path.open("wb") as output:
            while chunk := file.file.read(_CHUNK_SIZE):
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError(f"File exceeds the maximum allowed size of {get_settings().max_upload_size_mb}MB.")
                output.write(chunk)
    except ValueError:
        absolute_path.unlink(missing_ok=True)
        raise
    return relative_path.as_posix(), size


def generated_pdf_target(category: str, owner_id: str, file_id: str) -> tuple[str, Path]:
    relative_path = Path(category) / owner_id / f"{file_id}.pdf"
    absolute_path = upload_root() / relative_path
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    return relative_path.as_posix(), absolute_path


def stored_file_path(relative_path: str) -> Path:
    return upload_root() / relative_path
