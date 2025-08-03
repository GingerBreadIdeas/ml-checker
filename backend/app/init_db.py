import logging
from sqlalchemy.orm import Session

from .core.security import get_password_hash
from .models import User, Organization

logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    # Create test user if it doesn't exist
    user = db.query(User).filter(User.email == "test@testemail.com").first()
    if not user:
        logger.info("Creating test user")
        test_user = User(
            username="testusername",
            email="test@testemail.com",
            hashed_password=get_password_hash("testpassword"),
            is_active=True,
            is_superuser=True,
        )
        db.add(test_user)
        db.commit()
        logger.info("Test user created")
    else:
        logger.info("Test user already exists")
