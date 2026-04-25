"""Database bootstrap utilities."""

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import break_entry, gps_point, trip, user  # noqa: F401
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def init_db() -> None:
    """Create all tables and seed an initial demo user."""
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == settings.demo_username).first()
        if not existing:
            seeded_user = User(
                username=settings.demo_username,
                password_hash=pwd_context.hash(settings.demo_password),
            )
            db.add(seeded_user)
            db.commit()
    finally:
        db.close()
