import os
import secrets
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_default_settlement_code() -> str:
    """Get settlement code from env var or generate a random secure default."""
    return os.environ.get("SETTLEMENT_CODE", secrets.token_hex(8).upper())


def get_default_init_code() -> str:
    """Get init code from env var or generate a random secure default."""
    return os.environ.get("INIT_CODE", secrets.token_hex(8).upper())