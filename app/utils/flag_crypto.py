"""
app/utils/flag_crypto.py — Military-grade flag hashing and validation.

Rules:
  - Raw flags are NEVER stored in the DB (only SHA-256 hex-digest).
  - Comparison uses hmac.compare_digest() to prevent timing attacks.
  - Submissions are normalised (strip, optional lowercase) before hashing.
"""
import hashlib
import hmac


def hash_flag(flag: str, lowercase: bool = False) -> str:
    """Return SHA-256 hex-digest of *flag* (64 hex chars).

    Args:
        flag: The raw flag string.
        lowercase: If True, normalise the flag to lowercase before hashing.
                   Set this to True on challenges that are case-insensitive.
    """
    normalised = flag.strip()
    if lowercase:
        normalised = normalised.lower()
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


def verify_flag(submitted: str, stored_hash: str, lowercase: bool = False) -> bool:
    """Timing-safe comparison between a submitted flag and a stored hash.

    Args:
        submitted: Raw string from the user's form input.
        stored_hash: SHA-256 hex-digest retrieved from the database.
        lowercase: Whether to normalise the submission before hashing.

    Returns:
        True if the submission matches, False otherwise.
    """
    submitted_hash = hash_flag(submitted, lowercase=lowercase)
    # hmac.compare_digest prevents timing-based enumeration of the flag
    return hmac.compare_digest(submitted_hash.encode(), stored_hash.encode())
