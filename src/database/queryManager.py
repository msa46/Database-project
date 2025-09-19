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
    def get_all_ingredients() -> List[Ingredient]:
        """Get all ingredients."""
        return Ingredient.select()[:]

    @staticmethod
    @db_session
    def get_all_pizzas() -> List[Pizza]:
        """Get all pizzas."""
        return Pizza.select()[:]
    
    @staticmethod
    @db_session
    def get_vegan_pizzas() -> List[Pizza]:
        """Get all pizzas that are vegan (all ingredients are vegan)."""
        return Pizza.select(p for p in Pizza if all(i.type == IngredientType.Vegan for i in p.ingredients))[:]

    @staticmethod
    @db_session
    def get_vegetarian_pizzas() -> List[Pizza]:
        """Get all pizzas that are vegetarian (all ingredients are vegan or vegetarian)."""
        return Pizza.select(p for p in Pizza if all(i.type in [IngredientType.Vegan, IngredientType.Vegetarian] for i in p.ingredients))[:]
    
# Calculates pizza price based on ingredient costs, margin and VAT
    @staticmethod
    @db_session
    def calculate_pizza_price(pizza_id: int) -> float:
        """Calculate pizza price: ingredient cost + 40% margin + 9% VAT."""
        pizza = Pizza.get(id=pizza_id)
        if not pizza:
            raise ValueError(f"Pizza with id {pizza_id} not found")
        ingredient_cost = sum(ing.price for ing in pizza.ingredients)
        with_margin = ingredient_cost * 1.40
        with_vat = with_margin * 1.09
        return round(with_vat, 2)

    @staticmethod
    @db_session
    def count_extras_by_type(extra_type: ExtraType) -> int:
        """Example: Count extras by type."""
        return Extra.select(e for e in Extra if e.type == extra_type).count()
