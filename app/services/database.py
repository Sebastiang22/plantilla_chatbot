"""This file contains the database service for the application."""

from typing import (
    List,
    Optional,
    Dict,
    Any,
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
from models.order import Order


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
                echo=False,  # Enable SQL query logging
            )


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

    async def update_user_name(self, user_id: int, name: str) -> User:
        """Actualiza el nombre de un usuario."""
        with Session(self.engine) as session:
            user = session.get(User, user_id)
            if user:
                user.name = name
                session.add(user)
                session.commit()
                session.refresh(user)
                logger.info("user_name_updated", user_id=user_id, new_name=name)
            return user

    async def get_user_details_with_latest_order(self, phone: str) -> Dict[str, Any]:
        """Obtiene el nombre del usuario y la dirección de su último pedido si está disponible.
        
        Args:
            phone: Número telefónico del usuario
            
        Returns:
            Dict[str, Any]: Diccionario con el nombre del usuario y la dirección del último pedido
        """
        # Preparar resultado por defecto
        result = {
            "name": None,
            "address": None,
            "user_id": None,
            "has_order": False
        }
        
        try:
            with Session(self.engine) as session:
                # Buscar el usuario por teléfono
                user_statement = select(User).where(User.phone == phone)
                user = session.exec(user_statement).first()
                
                if not user:
                    logger.warn(f"Usuario no encontrado con teléfono: {phone}")
                    return result
                
                # Actualizar resultado con datos del usuario
                result["name"] = user.name
                result["user_id"] = user.id
                
                logger.info(f"Usuario encontrado: {user.name} (ID: {user.id})")
                
                # IMPORTANTE: Buscar la orden usando el número de teléfono como customer_id
                # Ya que es lo que se guarda en la base de datos según la imagen
                try:
                    # Buscar orden usando el teléfono (que es lo que se usa como customer_id)
                    order_statement = (
                        select(Order)
                        .where(Order.customer_id == phone)  # Usar phone directamente
                        .order_by(Order.created_at.desc())
                        .limit(1)
                    )
                    
                    logger.info(f"Buscando órdenes con customer_id={phone}")
                    latest_order = session.exec(order_statement).first()
                    
                    # Si se encontró una orden
                    if latest_order:
                        logger.info(f"Orden encontrada: ID={latest_order.id}, Address={latest_order.address!r}")
                        result["has_order"] = True
                        
                        # Verificar si la dirección tiene valor
                        if latest_order.address and latest_order.address.strip():
                            result["address"] = latest_order.address.strip()
                            logger.info(f"Dirección encontrada: {result['address']!r}")
                        else:
                            logger.warn("La dirección en la orden está vacía")
                        
                        # Incluir detalles de la orden
                        result["order"] = {
                            "order_id": str(latest_order.id),
                            "status": latest_order.status,
                            "customer_id": latest_order.customer_id,
                            "address": result["address"],
                            "total_amount": latest_order.total_amount,
                            "created_at": latest_order.created_at.isoformat() if latest_order.created_at else None
                        }
                    else:
                        logger.warn(f"No se encontraron órdenes para el teléfono {phone}")
                except Exception as e:
                    logger.error(f"Error al buscar órdenes: {str(e)}")
                    # No propagar el error, ya tenemos la información del usuario
        
        except Exception as e:
            logger.error(f"Error general en get_user_details_with_latest_order: {str(e)}")
        
        # Log final de la respuesta
        logger.info(f"Respuesta completa: {result}")
        return result


# Create a singleton instance
database_service = DatabaseService()
