"""
app/utils/file_utils.py — Secure file upload handling.
Validates extension, generates safe filenames, enforces size limits.
"""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


ALLOWED_EXTENSIONS = {"zip", "txt", "png", "jpg", "jpeg", "pdf", "bin", "tar", "gz", "pcap"}


def allowed_file(filename: str) -> bool:
    """Return True if the file extension is in the allowlist."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_challenge_file(file) -> tuple[str, str]:
    """Save an uploaded challenge file securely.

    Returns:
        (relative_path, original_filename) suitable for storing in DB.
    Raises:
        ValueError: if file type is not allowed.
    """
    original_name = secure_filename(file.filename)
    if not original_name or not allowed_file(original_name):
        raise ValueError(f"File type not allowed: {original_name}")

    ext = original_name.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    dest_path = os.path.join(upload_dir, unique_name)
    file.save(dest_path)

    # Return relative path (relative to static/)
    rel_path = f"uploads/{unique_name}"
    return rel_path, original_name


def delete_challenge_file(relative_path: str) -> bool:
    """Delete a challenge file from disk. Returns True on success."""
    if not relative_path:
        return False
    full_path = os.path.join(
        current_app.root_path, "static", relative_path
    )
    if os.path.isfile(full_path):
        os.remove(full_path)
        return True
    return False
