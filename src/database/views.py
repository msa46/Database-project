from typing import List, Dict, Any, Optional
from enum import Enum
from pony.orm import db_session
import logging

from .models import (
    IngredientType, Pizza, Extra
)

# Configure logging
logger = logging.getLogger(__name__)


class DietaryFilter(Enum):
    """Dietary filter options for menu items."""
    ALL = "all"
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    NORMAL = "normal"


class MenuView:
    """View class for menu-related operations including pricing and filtering."""

    @staticmethod
    @db_session
    def get_menu_items_with_prices_and_filters(dietary_filter: DietaryFilter = DietaryFilter.ALL) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all menu items (pizzas and extras) with calculated prices and dietary filtering.

        Args:
            dietary_filter: Filter for dietary requirements

        Returns:
            Dictionary containing pizzas and extras with their details and prices
        """
        pizzas = MenuView.get_pizzas_with_prices_and_filters(dietary_filter)
        extras = MenuView.get_extras_with_prices()

        return {
            'pizzas': pizzas,
            'extras': extras
        }

    @staticmethod
    @db_session
    def get_pizzas_with_prices_and_filters(dietary_filter: DietaryFilter = DietaryFilter.ALL) -> List[Dict[str, Any]]:
        """
        Get all pizzas with calculated prices and dietary classification.

        Args:
            dietary_filter: Filter for dietary requirements

        Returns:
            List of pizzas with price and dietary information
        """
        pizzas = list(Pizza.select())

        # Apply dietary filtering
        if dietary_filter == DietaryFilter.VEGAN:
            pizzas = [p for p in pizzas if all(i.type == IngredientType.Vegan for i in p.ingredients)]
        elif dietary_filter == DietaryFilter.VEGETARIAN:
            pizzas = [p for p in pizzas if all(i.type in [IngredientType.Vegan, IngredientType.Vegetarian] for i in p.ingredients)]

        result = []
        for pizza in pizzas:
            price = MenuView.calculate_pizza_price(pizza.id)
            dietary_type = MenuView.get_pizza_dietary_type(pizza)

            pizza_data = {
                'id': pizza.id,
                'name': pizza.name,
                'description': pizza.description,
                'price': round(price, 2),
                'dietary_type': dietary_type.value,
                'ingredients': [
                    {
                        'name': ing.name,
                        'price': ing.price,
                        'type': ing.type.value
                    } for ing in pizza.ingredients
                ],
                'stock': pizza.stock
            }
            result.append(pizza_data)

        return result

    @staticmethod
    @db_session
    def get_extras_with_prices() -> List[Dict[str, Any]]:
        """
        Get all extras with their prices.

        Returns:
            List of extras with price information
        """
        extras = list(Extra.select())

        result = []
        for extra in extras:
            extra_data = {
                'id': extra.id,
                'name': extra.name,
                'price': round(extra.price, 2),
                'type': extra.type.value
            }
            result.append(extra_data)

        return result

    @staticmethod
    @db_session
    def calculate_pizza_price(pizza_id: int) -> float:
        """
        Calculate pizza price: ingredient cost + 40% margin + 9% VAT.

        Args:
            pizza_id: ID of the pizza to calculate price for

        Returns:
            Calculated price rounded to 2 decimal places
        """
        pizza = Pizza.get(id=pizza_id)
        if not pizza:
            raise ValueError(f"Pizza with id {pizza_id} not found")

        ingredient_cost = sum(ing.price for ing in pizza.ingredients)
        with_margin = ingredient_cost * 1.40
        with_vat = with_margin * 1.09
        return round(with_vat, 2)

    @staticmethod
    @db_session
    def get_pizza_dietary_type(pizza: Pizza) -> IngredientType:
        """
        Determine the dietary type of a pizza based on its ingredients.

        Args:
            pizza: Pizza entity to analyze

        Returns:
            The most restrictive dietary type (Vegan > Vegetarian > Normal)
        """
        ingredient_types = [ing.type for ing in pizza.ingredients]

        if all(t == IngredientType.Vegan for t in ingredient_types):
            return IngredientType.Vegan
        elif all(t in [IngredientType.Vegan, IngredientType.Vegetarian] for t in ingredient_types):
            return IngredientType.Vegetarian
        else:
            return IngredientType.Normal

    @staticmethod
    @db_session
    def get_vegan_pizzas_with_prices() -> List[Dict[str, Any]]:
        """
        Get all vegan pizzas with calculated prices.

        Returns:
            List of vegan pizzas with price and ingredient details
        """
        return MenuView.get_pizzas_with_prices_and_filters(DietaryFilter.VEGAN)

    @staticmethod
    @db_session
    def get_vegetarian_pizzas_with_prices() -> List[Dict[str, Any]]:
        """
        Get all vegetarian pizzas with calculated prices.

        Returns:
            List of vegetarian pizzas with price and ingredient details
        """
        return MenuView.get_pizzas_with_prices_and_filters(DietaryFilter.VEGETARIAN)

    @staticmethod
    @db_session
    def get_available_pizzas_with_prices() -> List[Dict[str, Any]]:
        """
        Get pizzas that are currently in stock with calculated prices.

        Returns:
            List of available pizzas with their details and prices
        """
        all_pizzas = list(Pizza.select())
        pizzas = [p for p in all_pizzas if p.stock > 0]
        result = []

        for pizza in pizzas:
            price = MenuView.calculate_pizza_price(pizza.id)
            dietary_type = MenuView.get_pizza_dietary_type(pizza)

            pizza_data = {
                'id': pizza.id,
                'name': pizza.name,
                'description': pizza.description,
                'price': round(price, 2),
                'dietary_type': dietary_type.value,
                'ingredients': [
                    {
                        'name': ing.name,
                        'price': ing.price,
                        'type': ing.type.value
                    } for ing in pizza.ingredients
                ],
                'stock': pizza.stock
            }
            result.append(pizza_data)

        return result