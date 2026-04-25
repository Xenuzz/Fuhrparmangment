"""Authentication and JWT services."""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Provides user auth and token generation methods."""

    @staticmethod
    def verify_password(plain_password: str, password_hash: str) -> bool:
        """Check plain password against its hash."""
        return pwd_context.verify(plain_password, password_hash)

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> User | None:
        """Load user by username."""
        return db.query(User).filter(User.username == username).first()

    @classmethod
    def authenticate_user(cls, db: Session, username: str, password: str) -> User | None:
        """Authenticate a user by username and password."""
        user = cls.get_user_by_username(db, username)
        if not user:
            return None
        if not cls.verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def create_access_token(subject: str) -> str:
        """Create signed JWT access token."""
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
        payload = {"sub": subject, "exp": expire}
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    @staticmethod
    def decode_access_token(token: str) -> str | None:
        """Decode JWT and return the subject username."""
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            return payload.get("sub")
        except JWTError:
            return None
