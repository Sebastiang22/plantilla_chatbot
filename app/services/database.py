"""This file contains the database service for the application."""

from typing import (
    List,
    Optional,
)

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import QueuePool
from sqlmodel import (
    Session,
    SQLModel,
    create_engine,
    select,
)

from core.config import (
    Environment,
    settings,
)
from core.logging import logger
from models.user import User
from models.thread import Thread


class DatabaseService:
    """Service class for database operations.

    This class handles all database operations for Users, Sessions, and Messages.
    It uses SQLModel for ORM operations and maintains a connection pool.
    """

    def __init__(self):
        """Initialize database service with connection pool."""
        try:
            # Configure environment-specific database connection pool settings
            pool_size = settings.POSTGRES_POOL_SIZE
            max_overflow = settings.POSTGRES_MAX_OVERFLOW

            # Create engine with appropriate pool configuration
            self.engine = create_engine(
                settings.POSTGRES_URL,
                pool_pre_ping=True,
                poolclass=QueuePool,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_timeout=30,  # Connection timeout (seconds)
                pool_recycle=1800,  # Recycle connections after 30 minutes
                echo=True,  # Enable SQL query logging
            )

            # Create tables (only if they don't exist)
            with Session(self.engine) as session:
                # Drop all tables first (only in development)
                if settings.ENVIRONMENT == Environment.DEVELOPMENT:
                    SQLModel.metadata.drop_all(self.engine)
                
            # Create all tables
            SQLModel.metadata.create_all(self.engine)
                
            # Verify tables exist
            with Session(self.engine) as session:
                session.exec(select(1)).first()

            logger.info(
                "database_initialized",
                environment=settings.ENVIRONMENT.value,
                pool_size=pool_size,
                max_overflow=max_overflow,
            )
        except SQLAlchemyError as e:
            logger.error("database_initialization_error", error=str(e), environment=settings.ENVIRONMENT.value)
            # In production, don't raise - allow app to start even with DB issues
            if settings.ENVIRONMENT != Environment.PRODUCTION:
                raise


    async def get_user_by_phone(self, phone: str) -> Optional[User]:
        """Get a user by phone.

        Args:
            phone: The phone of the user to retrieve

        Returns:
            Optional[User]: The user if found, None otherwise
        """
        with Session(self.engine) as session:
            statement = select(User).where(User.phone == phone)
            user = session.exec(statement).first()
            return user

    async def create_user(self, name: str, phone: str) -> User:
        """Create a new user.

        Args:
            name: User's name
            phone: User's phone number

        Returns:
            User: The created user
        """
        with Session(self.engine) as session:
            user = User(name=name, phone=phone)
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info("user_created", phone=phone)
            return user

    async def get_latest_thread(self, user_id: int) -> Optional[Thread]:
        """Get the latest thread for a user.

        Args:
            user_id: The ID of the user

        Returns:
            Optional[Thread]: The latest thread if exists, None otherwise
        """
        with Session(self.engine) as session:
            statement = (
                select(Thread)
                .where(Thread.user_id == user_id)
                .order_by(Thread.created_at.desc())
                .limit(1)
            )
            thread = session.exec(statement).first()
            return thread

    async def create_thread(self, thread_id: str, user_id: int) -> Thread:
        """Create a new thread.

        Args:
            thread_id: The ID for the new thread
            user_id: The ID of the user who owns the thread

        Returns:
            Thread: The created thread
        """
        with Session(self.engine) as session:
            thread = Thread(id=thread_id, user_id=user_id)
            session.add(thread)
            session.commit()
            session.refresh(thread)
            logger.info("thread_created", thread_id=thread_id, user_id=user_id)
            return thread

    def get_session_maker(self):
        """Get a session maker for creating database sessions.

        Returns:
            Session: A SQLModel session maker
        """
        return Session(self.engine)

    async def health_check(self) -> bool:
        """Check database connection health.

        Returns:
            bool: True if database is healthy, False otherwise
        """
        try:
            with Session(self.engine) as session:
                # Execute a simple query to check connection
                session.exec(select(1)).first()
                return True
        except Exception as e:
            logger.error("database_health_check_failed", error=str(e))
            return False


# Create a singleton instance
database_service = DatabaseService()
