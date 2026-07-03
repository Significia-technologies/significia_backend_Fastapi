"""
Rotate ENCRYPTION_KEY: re-encrypt all Fernet-encrypted columns with a new key.

Run this ONCE, after generating a new ENCRYPTION_KEY, but BEFORE deploying that
new key to the running app. It decrypts every affected column using the OLD key
(passed explicitly here, not read from settings) and re-encrypts with the NEW
key currently configured in app.core.config.settings / ENCRYPTION_KEY env var.

Usage:
    OLD_ENCRYPTION_KEY="change-this-to-a-secure-32-byte-base64-key-in-production" \
    python scripts/rotate_encryption_key.py

If a row's ciphertext fails to decrypt with the old key (e.g. it was already
plaintext, empty, or encrypted with some other key), it is left untouched and
logged as skipped.
"""
import base64
import hashlib
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.ia_master import IAMaster
from app.models.email_settings import EmailSettings
from app.utils.encryption import encrypt_string


def _fernet_primary(key: str) -> Fernet:
    key_hash = hashlib.sha256(key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_hash))


def _fernet_legacy(key: str) -> Fernet:
    padded = key.ljust(32, "0") if len(key) < 32 else key
    return Fernet(base64.urlsafe_b64encode(padded[:32].encode()))


def decrypt_with_key(value: str, key: str) -> str | None:
    """Try both known derivations of the OLD key. Returns None if neither works."""
    if not value or not value.startswith("gAAAA"):
        return None
    for fernet in (_fernet_primary(key), _fernet_legacy(key)):
        try:
            return fernet.decrypt(value.encode()).decode()
        except InvalidToken:
            continue
    return None


IA_MASTER_FIELDS = [
    "name_of_ia",
    "name_of_entity",
    "registered_address",
    "registered_contact_number",
    "registered_email_id",
    "ia_registration_number",
    "ia_logo_path",
]


def rotate(old_key: str):
    db: Session = SessionLocal()
    stats = {"updated": 0, "skipped": 0}
    try:
        for row in db.query(IAMaster).all():
            changed = False
            for field in IA_MASTER_FIELDS:
                current = getattr(row, field, None)
                plaintext = decrypt_with_key(current, old_key)
                if plaintext is None:
                    continue
                setattr(row, field, encrypt_string(plaintext))
                changed = True
            if changed:
                stats["updated"] += 1
            else:
                stats["skipped"] += 1

        for row in db.query(EmailSettings).all():
            plaintext = decrypt_with_key(row.smtp_password_encrypted, old_key)
            if plaintext is not None:
                row.smtp_password_encrypted = encrypt_string(plaintext)
                stats["updated"] += 1
            else:
                stats["skipped"] += 1

        db.commit()
        print(f"Rotation complete. Rows updated: {stats['updated']}, skipped: {stats['skipped']}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    old_key = os.environ.get("OLD_ENCRYPTION_KEY")
    if not old_key:
        print("Set OLD_ENCRYPTION_KEY env var to the previously-used ENCRYPTION_KEY value.")
        sys.exit(1)
    rotate(old_key)
