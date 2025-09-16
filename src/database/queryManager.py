from datetime import datetime
from typing import List, Dict, Any, Optional
from pony.orm import db_session, select, desc, count

from .models import (
    IngredientType, ExtraType, DeliveryStatus, OrderStatus,
    OrderPizzaRelation, Pizza, Extra, Ingredient, User,
    Customer, Employee, DeliveryPerson, Order, DiscountCode
)


class QueryManager:
    """Query manager with examples for ExtraType."""

    @staticmethod
    @db_session
    def get_extras_by_type(extra_type: ExtraType) -> List[Extra]:
        """Example: Get extras by type."""
        return Extra.select(e for e in Extra if e.type == extra_type)[:]

    @staticmethod
    @db_session
    def get_all_drinks() -> List[Extra]:
        """Example: Get all drink extras."""
        return Extra.select(e for e in Extra if e.type == ExtraType.Drink)[:]

    @staticmethod
    @db_session
    def get_all_desserts() -> List[Extra]:
        """Example: Get all dessert extras."""
        return Extra.select(e for e in Extra if e.type == ExtraType.Dessert)[:]

    @staticmethod
    @db_session
    def count_extras_by_type(extra_type: ExtraType) -> int:
        """Example: Count extras by type."""
        return Extra.select(e for e in Extra if e.type == extra_type).count()