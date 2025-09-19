from datetime import datetime, date
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

    #TODO: Check if this has all the options needed, since there are many optional fields
    @staticmethod
    @db_session
    def add_customer(username: str, email: str, password: str, birthday_order: bool, loyalty_points: int = 0, phone: Optional[str] = None, address: Optional[str] = None, postal_code: Optional[str] = None, birthdate: Optional[date] = None, gender: Optional[str] = None) -> Customer:
        """Add a new customer to the database with all available options."""
        customer_data = {
            'username': username,
            'email': email,
            'birthday_order': birthday_order,
            'loyalty_points': loyalty_points
        }

        # Add optional fields only if they are provided
        if phone is not None:
            customer_data['phone'] = phone
        if address is not None:
            customer_data['address'] = address
        if postal_code is not None:
            customer_data['postalCode'] = postal_code
        if birthdate is not None:
            customer_data['birthdate'] = birthdate
        if gender is not None:
            customer_data['Gender'] = gender

        customer = Customer(**customer_data)
        customer.set_password(password)
        return customer

    #TODO: Check if everything gets removed properly (orders, discount codes, etc.)
    @staticmethod
    @db_session
    def remove_customer(username: str) -> bool:
        """Remove a customer from the database by username."""
        customer = Customer.get(username=username)
        if customer:
            customer.delete()
            return True
        return False

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
