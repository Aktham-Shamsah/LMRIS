from __future__ import annotations
from pathlib import Path
from fastapi import UploadFile
from config import get_settings

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

_CHUNK_SIZE = 1024 * 1024


def _upload_root() -> Path:
    root = Path(__file__).resolve().parent.parent / get_settings().upload_dir
    root.mkdir(parents=True, exist_ok=True)
    return root


def validate_upload(file: UploadFile) -> str:
    """Returns the validated lowercase extension, or raises ValueError."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext or 'unknown'}'. "
            f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Unsupported content type '{file.content_type}'.")
    return ext


def save_attachment(application_id: str, doc_id: str, file: UploadFile, ext: str) -> tuple[str, int]:
    """Streams the upload to disk, enforcing the configured size limit.
    Returns (relative_path, size_bytes). Raises ValueError if too large."""
    app_dir = _upload_root() / application_id
    app_dir.mkdir(parents=True, exist_ok=True)
    relative_path = f"{application_id}/{doc_id}{ext}"
    dest = app_dir / f"{doc_id}{ext}"
    max_bytes = get_settings().max_upload_size_mb * 1024 * 1024

    size = 0
    try:
        with dest.open("wb") as out:
            while chunk := file.file.read(_CHUNK_SIZE):
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError(
                        f"File exceeds the maximum allowed size of {get_settings().max_upload_size_mb}MB."
                    )
                out.write(chunk)
    except ValueError:
        dest.unlink(missing_ok=True)
        raise
    return relative_path, size


def delete_attachment_file(relative_path: str) -> None:
    (_upload_root() / relative_path).unlink(missing_ok=True)


def attachment_path(relative_path: str) -> Path:
    return _upload_root() / relative_path
