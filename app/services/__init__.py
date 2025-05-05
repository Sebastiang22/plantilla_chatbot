"""This file contains the services for the application."""

from services.database import database_service
from services.order_service import order_service
from services.inventory_service import inventory_service

__all__ = ["database_service", "order_service", "inventory_service"]
