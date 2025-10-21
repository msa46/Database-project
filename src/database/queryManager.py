from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from pony.orm import db_session, select, desc, count, avg, commit
import re
import secrets
import logging
import traceback
import random

from .models import (
    IngredientType, ExtraType, DeliveryStatus, OrderStatus,
    OrderPizzaRelation, Pizza, Extra, Ingredient, User,
    Customer, Employee, DeliveryPerson, Order, DiscountCode
)

# Configure logging
logger = logging.getLogger(__name__)

class QueryManager:
    """Query manager with examples for ExtraType."""

# -=-=-=-=-=- BASIC MENU QUERIES -=-=-=-=-=- #
    @staticmethod
    @db_session
    def get_extras_by_type(extra_type: ExtraType) -> List[Extra]:
        """Example: Get extras by type."""
        return list(Extra.select(lambda e: e.type == extra_type))

    @staticmethod
    @db_session
    def get_all_drinks() -> List[Extra]:
        """Example: Get all drink extras."""
        # Fetch all extras and filter in Python due to Pony ORM limitations
        all_extras = list(Extra.select())
        return [e for e in all_extras if e.type == ExtraType.Drink]

    @staticmethod
    @db_session
    def get_all_desserts() -> List[Extra]:
        """Example: Get all dessert extras."""
        # Fetch all extras and filter in Python due to Pony ORM limitations
        all_extras = list(Extra.select())
        return [e for e in all_extras if e.type == ExtraType.Dessert]

    @staticmethod
    @db_session
    def get_all_ingredients() -> List[Ingredient]:
        """Get all ingredients."""
        return list(Ingredient.select()[:])

    @staticmethod
    @db_session
    def get_all_pizzas() -> List[Pizza]:
        """Get all pizzas."""
        return list(Pizza.select()[:])
    
    @staticmethod
    @db_session
    def get_pizzas_paginated(page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """Get pizzas with pagination.
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            
        Returns:
            Dictionary with pizzas list, pagination info, and total count
        """
        try:
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Get total count
            total_count = Pizza.select().count()
            
            # Get all pizzas first, then slice
            all_pizzas = list(Pizza.select())
            pizzas = all_pizzas[offset:offset + page_size]
            
            # Calculate pagination info
            total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "pizzas": pizzas,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                }
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in get_pizzas_paginated: {str(e)}")
            logger.error(f"Page: {page}, Page size: {page_size}")
            raise
    
    @staticmethod
    @db_session
    def get_vegan_pizzas() -> List[Pizza]:
        """Get all pizzas that are vegan (all ingredients are vegan)."""
        # This is a complex query that needs to be done in two steps due to Pony ORM limitations
        all_pizzas = list(Pizza.select(lambda p: p.ingredients))
        vegan_pizzas = []
        for pizza in all_pizzas:
            if pizza.ingredients and all(i.type == IngredientType.Vegan for i in list(pizza.ingredients)):
                vegan_pizzas.append(pizza)
        return vegan_pizzas
    
    @staticmethod
    @db_session
    def get_vegetarian_pizzas() -> List[Pizza]:
        """Get all pizzas that are vegetarian (all ingredients are vegan or vegetarian)."""
        # This is a complex query that needs to be done in two steps due to Pony ORM limitations
        all_pizzas = list(Pizza.select(lambda p: p.ingredients))
        vegetarian_pizzas = []
        for pizza in all_pizzas:
            if pizza.ingredients and all(i.type in [IngredientType.Vegan, IngredientType.Vegetarian] for i in list(pizza.ingredients)):
                vegetarian_pizzas.append(pizza)
        return vegetarian_pizzas

    @staticmethod
    @db_session
    def get_pizza_ingredients(pizza_id: int) -> List[Ingredient]:
        """Get all ingredients for a specific pizza by pizza ID."""
        pizza = Pizza.get(id=pizza_id)
        if not pizza:
            raise ValueError(f"Pizza with id {pizza_id} not found")
        return list(pizza.ingredients)

    @staticmethod
    @db_session
    def calculate_pizza_price(pizza_id: int) -> float:
        """Calculate pizza price: ingredient cost + 40% margin + 9% VAT."""
        pizza = Pizza.get(id=pizza_id)
        if not pizza:
            raise ValueError(f"Pizza with id {pizza_id} not found")
        # Handle case where pizza might have no ingredients
        if not pizza.ingredients:
            return 0.0
        ingredient_cost = sum(ing.price for ing in list(pizza.ingredients))
        with_margin = ingredient_cost * 1.40
        with_vat = with_margin * 1.09
        return round(with_vat, 2)

    @staticmethod
    @db_session
    def count_extras_by_type(extra_type: ExtraType) -> int:
        """Example: Count extras by type."""
        # Fetch all extras and filter in Python due to Pony ORM limitations
        all_extras = list(Extra.select())
        return sum(1 for e in all_extras if e.type == extra_type)

# -=-=-=-=-=- USER QUERIES -=-=-=-=-=- #

    @staticmethod
    @db_session
    def add_user(username: str,
                 email: str,
                 password: str,
                 phone: Optional[str] = None,
                 address: Optional[str] = None,
                 postal_code: Optional[str] = None,
                 birthdate: Optional[date] = None,
                 gender: Optional[str] = None,
                 # Customer specific
                 birthday_order: Optional[bool] = None,
                 loyalty_points: Optional[int] = None,
                 # Employee specific
                 position: Optional[str] = None,
                 salary: Optional[float] = None,
                 # DeliveryPerson specific
                 status: Optional[DeliveryStatus] = None) -> User:
        """Add a new user to the database. The type of user (Customer, Employee, DeliveryPerson, or base User)
        is determined by the parameters provided. Always creates a base User first, then 'updates' to the specific type."""

        # Hash the password first
        password_hash, salt = User.hash_password(password)
        
        # Base user data
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'salt': salt
        }

        # Add optional base fields
        if phone is not None:
            user_data['phone'] = phone
        if address is not None:
            user_data['address'] = address
        if postal_code is not None:
            user_data['postalCode'] = postal_code
        if birthdate is not None:
            user_data['birthdate'] = birthdate
        if gender is not None:
            user_data['Gender'] = gender

        # Determine user type based on provided parameters
        if status is not None:
            # DeliveryPerson
            user_data['position'] = position or ''
            user_data['salary'] = salary or 0.0
            user_data['status'] = status
            user = DeliveryPerson(**user_data)
        elif position is not None or salary is not None:
            # Employee
            user_data['position'] = position or ''
            user_data['salary'] = salary or 0.0
            user = Employee(**user_data)
        elif birthday_order is not None or loyalty_points is not None:
            # Customer
            user_data['birthday_order'] = birthday_order if birthday_order is not None else False
            user_data['loyalty_points'] = loyalty_points if loyalty_points is not None else 0
            user = Customer(**user_data)
        else:
            # Base User
            user = User(**user_data)

        return user

    @staticmethod
    @db_session
    def remove_user(username: str) -> bool:
        """Remove a user from the database by username. Works for any user type (Customer, Employee, DeliveryPerson, or base User)."""
        user = User.get(username=username)
        if user:
            user.delete()
            commit()
            return True
        return False

    @staticmethod
    @db_session
    def update_user(username: str,
                    email: Optional[str] = None,
                    phone: Optional[str] = None,
                    address: Optional[str] = None,
                    postal_code: Optional[str] = None,
                    birthdate: Optional[date] = None,
                    gender: Optional[str] = None,
                    # Customer specific
                    birthday_order: Optional[bool] = None,
                    loyalty_points: Optional[int] = None,
                    # Employee specific
                    position: Optional[str] = None,
                    salary: Optional[float] = None,
                    # DeliveryPerson specific
                    status: Optional[DeliveryStatus] = None) -> bool:
        """Update a user's information. Works for any user type and updates fields that exist on the user."""
        user = User.get(username=username)
        if not user:
            return False
    
        # Validate and update base fields if provided
        if email is not None:
            # Validate email format
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                raise ValueError("Invalid email format")
            # Check uniqueness
            existing = User.get(email=email)
            if existing and existing != user:
                raise ValueError("Email already in use")
            user.email = email
    
        if phone is not None:
            # Validate phone format
            clean = re.sub(r'[^\d+]', '', phone)
            if clean.startswith('+'):
                if not re.match(r'^\+[1-9][0-9]{6,14}$', clean):
                    raise ValueError("Invalid international phone format")
            else:
                if not re.match(r'^[0-9]{10}$', clean):
                    raise ValueError("Domestic phone must be exactly 10 digits")
            user.phone = phone
    
        if address is not None:
            if not address.strip():
                raise ValueError("Address cannot be empty")
            user.address = address
    
        if postal_code is not None:
            if not postal_code.strip():
                raise ValueError("Postal code cannot be empty")
            user.postalCode = postal_code
    
        if birthdate is not None:
            if not isinstance(birthdate, date):
                raise ValueError("Birthdate must be a date object")
            if birthdate > date.today():
                raise ValueError("Birthdate cannot be in the future")
            user.birthdate = birthdate
    
        if gender is not None:
            if not gender.strip():
                raise ValueError("Gender cannot be empty")
            user.Gender = gender
    
        # Validate and update type-specific fields if they exist on the user and are provided
        if hasattr(user, 'birthday_order') and birthday_order is not None:
            if not isinstance(birthday_order, bool):
                raise ValueError("Birthday order must be a boolean")
            user.birthday_order = birthday_order
    
        if hasattr(user, 'loyalty_points') and loyalty_points is not None:
            if not isinstance(loyalty_points, int) or loyalty_points < 0:
                raise ValueError("Loyalty points must be a non-negative integer")
            user.loyalty_points = loyalty_points
    
        if hasattr(user, 'position') and position is not None:
            if not position.strip():
                raise ValueError("Position cannot be empty")
            user.position = position
    
        if hasattr(user, 'salary') and salary is not None:
            if not isinstance(salary, (int, float)) or salary <= 0:
                raise ValueError("Salary must be a positive number")
            user.salary = salary
    
        if hasattr(user, 'status') and status is not None:
            user.status = status
    
        commit()
        return True

# -=-=-=-=-=- ORDER QUERIES -=-=-=-=-=- #
    @staticmethod
    @db_session
    def get_orders_by_user(user_id: int) -> List[Order]:
        """Get all orders for a specific user by user ID."""
        user = User.get(id=user_id)
        if not user:
            return []
        return list(user.orders)
    
    @staticmethod
    @db_session
    def create_order(
                     user_id: int,
                     pizza_quantities: List[List[int]],
                     extra_ids: Optional[List[int]] = None,
                     discount_code: Optional[str] = None,
                     status: OrderStatus = OrderStatus.Pending,
                     created_at: Optional[datetime] = None,
                     delivered_at: Optional[datetime] = None,
                     delivery_person_id: Optional[int] = None,
                     postal_code: Optional[str] = None
                     ) -> Order:
        """Create a new order with proper transaction management and at least one pizza and optional extras."""
        try:
            logger.debug(f"Starting transaction for order creation - user_id: {user_id}")

            # Validate input parameters
            if not user_id:
                raise ValueError("User ID is required")

            if not pizza_quantities or len(pizza_quantities) == 0:
                raise ValueError("At least one pizza is required")

            # Get user
            user = User.get(id=user_id)
            if not user:
                raise ValueError(f"User with id {user_id} not found")

            # Determine postal code
            final_postal_code = postal_code or user.postalCode
            if not final_postal_code:
                raise ValueError("Postal code must be provided or set on the user")

            # Determine created_at
            final_created_at = created_at or datetime.now()

            # Get delivery person if provided
            delivery_person = None
            if delivery_person_id:
                delivery_person = DeliveryPerson.get(id=delivery_person_id)
                if not delivery_person:
                    raise ValueError(f"Delivery person with id {delivery_person_id} not found")

            # Collect all pizza and extra IDs for batch fetching
            pizza_ids = [item[0] for item in pizza_quantities]
            extra_ids_set = set(extra_ids) if extra_ids else set()

            # Fetch all pizzas and extras in single queries
            pizzas = Pizza.select(lambda p: p.id in pizza_ids) if pizza_ids else []
            extras = Extra.select(lambda e: e.id in extra_ids_set) if extra_ids_set else []

            # Create dictionaries for O(1) lookups
            pizza_dict = {p.id: p for p in list(pizzas)}
            extra_dict = {e.id: e for e in list(extras)}

            # Validate all pizzas exist before creating order
            for pizza_id, quantity in pizza_quantities:
                if pizza_id not in pizza_dict:
                    raise ValueError(f"Pizza with id {pizza_id} not found")
                if quantity < 1:
                    raise ValueError(f"Invalid quantity {quantity} for pizza {pizza_id}. Must be at least 1")

            # Validate all extras exist before creating order
            if extra_ids:
                for extra_id in extra_ids:
                    if extra_id not in extra_dict:
                        raise ValueError(f"Extra with id {extra_id} not found")

            # Create the order
            logger.debug("Creating order entity within transaction")
            order = Order(
                user=user,
                status=status,
                postalCode=final_postal_code,
                created_at=final_created_at,
                delivered_at=delivered_at,
                delivery_person=delivery_person
            )

            # Add pizzas with quantities using dictionary lookup within transaction
            logger.debug(f"Adding {len(pizza_quantities)} pizzas to order")
            for item in pizza_quantities:
                pizza_id, quantity = item
                pizza = pizza_dict.get(pizza_id)
                OrderPizzaRelation(order=order, pizza=pizza, quantity=quantity)

            # Add extras if provided using dictionary lookup within transaction
            if extra_ids:
                logger.debug(f"Adding {len(extra_ids)} extras to order")
                for extra_id in extra_ids:
                    extra = extra_dict.get(extra_id)
                    order.extras.add(extra)

            # Calculate total order amount before applying discount
            total = 0.0

            # Calculate pizza costs
            for item in pizza_quantities:
                pizza_id, quantity = item
                pizza = pizza_dict.get(pizza_id)
                unit_price = QueryManager.calculate_pizza_price(pizza.id)
                total += unit_price * quantity

            # Calculate extra costs
            if extra_ids:
                for extra_id in extra_ids:
                    extra = extra_dict.get(extra_id)
                    total += extra.price

            # Apply discount code if provided
            discount_amount = 0.0
            discount_info = None

            if discount_code:
                logger.debug(f"Processing discount code: {discount_code}")
                # Get discount code details using existing query
                dc_details = QueryManager.get_discount_code_details(discount_code)

                if not dc_details or not dc_details.get('is_valid'):
                    raise ValueError(f"Invalid or expired discount code: {discount_code}")

                dc = DiscountCode.get(code=discount_code)
                if not dc:
                    raise ValueError(f"Discount code not found: {discount_code}")

                # Apply discount based on type
                if dc.percentage == 0.0:
                    # Birthday code: 1 free cheapest pizza + 1 free drink
                    logger.debug("Applying birthday discount (free cheapest pizza + 1 free drink)")

                    # Find cheapest pizza in order
                    cheapest_pizza = None
                    cheapest_price = float('inf')

                    for opr in order.pizza_relations:
                        pizza_price = QueryManager.calculate_pizza_price(opr.pizza.id)
                        if pizza_price < cheapest_price:
                            cheapest_price = pizza_price
                            cheapest_pizza = opr

                    # Find free drink (cheapest available drink extra)
                    free_drink = None
                    drink_price = float('inf')

                    for extra in order.extras:
                        if extra.type == ExtraType.Drink and extra.price < drink_price:
                            drink_price = extra.price
                            free_drink = extra

                    # Apply discounts
                    if cheapest_pizza:
                        discount_amount += cheapest_price
                        logger.debug(f"Applied free pizza discount: {cheapest_price}")

                    if free_drink:
                        discount_amount += free_drink.price
                        logger.debug(f"Applied free drink discount: {free_drink.price}")

                    discount_info = {
                        'code': dc.code,
                        'type': 'birthday',
                        'description': '1 free pizza (cheapest) and 1 free drink',
                        'amount': round(discount_amount, 2)
                    }

                else:
                    # Percentage-based discount
                    logger.debug(f"Applying percentage discount: {dc.percentage}%")
                    discount_amount = total * (dc.percentage / 100)
                    discount_info = {
                        'code': dc.code,
                        'type': 'loyalty',
                        'percentage': dc.percentage,
                        'amount': round(discount_amount, 2)
                    }

                # Mark discount code as used if it's a one-time use
                if dc.percentage == 0.0:  # Birthday codes are one-time use
                    dc.used = True
                    dc.used_by = user

            # Commit the transaction
            logger.debug("Committing order creation transaction")
            commit()

            logger.info(f"Order created successfully with ID: {order.id} for user: {user.username}")
            return order

        except Exception as e:
            logger.error(f"Error creating order for user_id {user_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Transaction will be automatically rolled back if commit() wasn't called
            raise

    @staticmethod
    @db_session
    def update_order(order_id: int,
                     status: Optional[OrderStatus] = None,
                     delivered_at: Optional[datetime] = None,
                     delivery_person_id: Optional[int] = None,
                     postal_code: Optional[str] = None
                     ) -> Order:
        """Update an existing order's details with proper transaction management."""
        try:
            logger.debug(f"Starting transaction for order update - order_id: {order_id}")

            # Validate input parameters
            if not order_id:
                raise ValueError("Order ID is required")

            # Get and validate order exists
            order = Order.get(id=order_id)
            if not order:
                raise ValueError(f"Order with id {order_id} not found")

            # Validate delivery person if provided
            if delivery_person_id is not None:
                delivery_person = DeliveryPerson.get(id=delivery_person_id)
                if not delivery_person:
                    raise ValueError(f"Delivery person with id {delivery_person_id} not found")

            # Update order fields within transaction
            logger.debug("Updating order fields within transaction")
            if status is not None:
                order.status = status
                # Automatically set delivered_at if status is Delivered and not set
                if status == OrderStatus.Delivered and order.delivered_at is None:
                    order.delivered_at = datetime.now()

            if delivered_at is not None:
                order.delivered_at = delivered_at

            if delivery_person_id is not None:
                delivery_person = DeliveryPerson.get(id=delivery_person_id)
                order.delivery_person = delivery_person

            if postal_code is not None:
                if not postal_code.strip():
                    raise ValueError("Postal code cannot be empty")
                order.postalCode = postal_code

            # Commit the transaction
            logger.debug("Committing order update transaction")
            commit()

            logger.info(f"Order {order_id} updated successfully")
            return order

        except Exception as e:
            logger.error(f"Error updating order {order_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Transaction will be automatically rolled back if commit() wasn't called
            raise
    
    @staticmethod
    @db_session
    def delete_order(order_id: int) -> bool:
        """Delete an order from the database with proper transaction management."""
        try:
            logger.debug(f"Starting transaction for order deletion - order_id: {order_id}")

            # Validate input parameters
            if not order_id:
                raise ValueError("Order ID is required")

            # Get and validate order exists
            order = Order.get(id=order_id)
            if not order:
                logger.warning(f"Order with id {order_id} not found for deletion")
                return False

            # Delete the order (this will cascade to OrderPizzaRelation and extras relationships)
            logger.debug("Deleting order within transaction")
            order.delete()

            # Commit the transaction
            logger.debug("Committing order deletion transaction")
            commit()

            logger.info(f"Order {order_id} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting order {order_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Transaction will be automatically rolled back if commit() wasn't called
            raise
    
    @staticmethod
    @db_session
    def get_order_confirmation(order_id: int) -> Optional[Dict[str, Any]]:
        """Get order confirmation details including total price and itemized list with prices."""
        order = Order.get(id=order_id)
        if not order:
            return None

        items = []
        total = 0.0

        # Calculate pizza costs
        for opr in list(order.pizza_relations):
            unit_price = QueryManager.calculate_pizza_price(opr.pizza.id)
            subtotal = unit_price * opr.quantity
            total += subtotal
            items.append({
                'type': 'pizza',
                'name': opr.pizza.name,
                'quantity': opr.quantity,
                'unit_price': round(unit_price, 2),
                'subtotal': round(subtotal, 2)
            })

        # Calculate extra costs
        for extra in list(order.extras):
            total += extra.price
            items.append({
                'type': 'extra',
                'name': extra.name,
                'quantity': 1,
                'unit_price': round(extra.price, 2),
                'subtotal': round(extra.price, 2)
            })
            
        # Apply discount if applicable
        discount_info = None
        if order.user.discount_code:
            dc = order.user.discount_code

            if dc.percentage == 0.0:
                # Birthday code: 1 free cheapest pizza + 1 free drink
                discount_amount = 0.0

                # Find cheapest pizza in order
                cheapest_pizza_price = float('inf')
                for opr in order.pizza_relations:
                    pizza_price = QueryManager.calculate_pizza_price(opr.pizza.id)
                    cheapest_pizza_price = min(cheapest_pizza_price, pizza_price)

                # Find cheapest drink in order
                cheapest_drink_price = float('inf')
                for extra in order.extras:
                    if extra.type == ExtraType.Drink:
                        cheapest_drink_price = min(cheapest_drink_price, extra.price)

                # Apply discounts
                if cheapest_pizza_price != float('inf'):
                    discount_amount += cheapest_pizza_price
                if cheapest_drink_price != float('inf'):
                    discount_amount += cheapest_drink_price

                discount_info = {
                    'code': dc.code,
                    'type': 'birthday',
                    'description': '1 free pizza (cheapest) and 1 free drink',
                    'amount': round(discount_amount, 2)
                }

            else:
                # Percentage-based discount
                discount_amount = total * (dc.percentage / 100)
                discount_info = {
                    'code': dc.code,
                    'type': 'loyalty',
                    'percentage': dc.percentage,
                    'amount': round(discount_amount, 2)
                }

            # Apply discount to total
            if discount_info:
                total -= discount_info['amount']

        return {
            'total_price': round(total, 2),
            'items': items,
            'discount': discount_info
        }

# -=-=-=-=-=- LOYALTY QUERIES -=-=-=-=-=- #

    @staticmethod
    @db_session
    def process_loyalty_points(user_id: int) -> Optional[DiscountCode]:
        """Process loyalty points after an order is completed with proper transaction management.
        Increments loyalty points for customers. If points reach 10,
        resets to 0 and creates a 10% discount code valid for 1 month."""
        try:
            logger.debug(f"Starting transaction for loyalty points processing - user_id: {user_id}")

            # Validate input parameters
            if not user_id:
                raise ValueError("User ID is required")

            # Get and validate user
            user = User.get(id=user_id)
            if not user:
                raise ValueError(f"User with id {user_id} not found")

            if not isinstance(user, Customer):
                logger.info(f"User {user_id} is not a customer, skipping loyalty points processing")
                return None

            # Process loyalty points within transaction
            logger.debug(f"Processing loyalty points for customer {user.username}")
            user.loyalty_points += 1

            discount_code = None
            if user.loyalty_points >= 10:
                logger.debug("Customer reached 10 loyalty points, creating discount code")
                now = datetime.now()
                valid_until = now + timedelta(days=30)
                code = secrets.token_hex(8).upper()

                dc = DiscountCode(
                    code=code,
                    percentage=10.0,
                    valid_until=valid_until,
                    valid_from=now,
                    used=False
                )
                user.loyalty_points = 0
                discount_code = dc

            # Commit the transaction
            logger.debug("Committing loyalty points processing transaction")
            commit()

            if discount_code:
                logger.info(f"Created discount code {code} for customer {user.username}")
            else:
                logger.info(f"Incremented loyalty points for customer {user.username}")

            return discount_code

        except Exception as e:
            logger.error(f"Error processing loyalty points for user {user_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Transaction will be automatically rolled back if commit() wasn't called
            raise

#PLEASE NOTE THAT: when precentage is 0.0, this means that its a birthday code. This would mean that you get 1 free pizza (cheapest) and 1 free drink
    @staticmethod
    @db_session
    def process_birthday_discounts() -> List[DiscountCode]:
        """Process birthday discounts at the start of each day.
        Finds customers with birthday today and creates discount codes
        for 1 free pizza and 1 free drink (percentage set to 0, special handling required)."""
        today = date.today()
        # Get all customers and filter in Python due to Pony ORM limitations
        all_customers = list(Customer.select())
        birthday_customers = []
        for c in all_customers:
            if c.birthdate and c.birthdate.month == today.month and c.birthdate.day == today.day:
                birthday_customers.append(c)
        discount_codes = []
        for customer in birthday_customers:
            now = datetime.now()
            valid_until = now + timedelta(days=7)
            code = secrets.token_hex(8).upper()
            dc = DiscountCode(
                code=code,
                percentage=0.0,  # Special case: free pizza and drink, not percentage-based
                valid_until=valid_until,
                valid_from=now,
                used=False
            )
            discount_codes.append(dc)
        commit()
        return discount_codes

    @staticmethod
    @db_session
    def get_discount_code_details(code: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a discount code."""
        dc = DiscountCode.get(code=code)
        if not dc:
            return None

        now = datetime.now()
        is_valid = (not dc.used and
                   (dc.valid_from is None or dc.valid_from <= now) and
                   dc.valid_until >= now)

        details = {
            'code': dc.code,
            'percentage': dc.percentage,
            'valid_from': dc.valid_from,
            'valid_until': dc.valid_until,
            'used': dc.used,
            'used_by': dc.used_by.username if dc.used_by else None,
            'is_valid': is_valid
        }

        # Determine discount type
        if dc.percentage == 0.0:
            details['type'] = 'birthday'
            details['description'] = '1 free pizza (cheapest) and 1 free drink'
        elif dc.percentage == 10.0:
            details['type'] = 'loyalty'
            details['description'] = '10% off next order'
        else:
            details['type'] = 'general'
            details['description'] = f'{dc.percentage}% off'

        return details

# -=-=-=-=-=- DELIVERY QUERIES -=-=-=-=-=- #

    @staticmethod
    @db_session
    def get_available_delivery_persons() -> List[DeliveryPerson]:
        """Get all delivery persons who are currently available for assignments."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Getting available delivery persons")
        # Fetch all delivery persons and filter in Python due to Pony ORM limitations
        all_delivery_persons = list(DeliveryPerson.select()[:])
        available_delivery_persons = [dp for dp in all_delivery_persons if dp.status == DeliveryStatus.Available]
        logger.info(f"Found {len(available_delivery_persons)} available delivery persons")
        return available_delivery_persons
        
    @staticmethod
    @db_session
    def update_delivery_person_status(delivery_person_id: int, new_status: DeliveryStatus) -> DeliveryPerson:
        """Update the status of a delivery person."""
        dp = DeliveryPerson.get(id=delivery_person_id)
        if not dp:
            raise ValueError(f"Delivery person with id {delivery_person_id} not found")
        dp.status = new_status
        commit()
        return dp
    
    @staticmethod
    @db_session
    def assign_delivery_person_to_order(order_id: int) -> Optional[Dict[str, Any]]:
        """Assign an available delivery person to an order with proper transaction management.
        Returns a dict with order_id and delivery_person_id if assignment was successful,
        None if no suitable delivery person found."""
        try:
            logger.debug(f"Starting transaction for delivery person assignment - order_id: {order_id}")

            # Validate input parameters
            if not order_id:
                raise ValueError("Order ID is required")

            # Get and validate order exists
            order = Order.get(id=order_id)
            if not order:
                raise ValueError(f"Order with id {order_id} not found")

            # Validate order state for assignment
            if order.delivery_person:
                raise ValueError("Order already has a delivery person assigned")

            if order.status != OrderStatus.In_Progress:
                raise ValueError("Order must be in progress to assign delivery person")

            # Find available delivery persons using the dedicated query
            logger.debug("Finding available delivery persons")
            available_dps = QueryManager.get_available_delivery_persons()
            if not available_dps:
                logger.info(f"No available delivery persons for order {order_id}")
                return None  # No available delivery person

            # Assign the first available delivery person within the same transaction
            logger.debug(f"Assigning delivery person {available_dps[0].id} to order {order_id}")
            dp = available_dps[0]
            order.delivery_person = dp
            dp.status = DeliveryStatus.On_Delivery

            # Commit the transaction
            logger.debug("Committing delivery person assignment transaction")
            commit()

            logger.info(f"Successfully assigned delivery person {dp.id} to order {order_id}")
            return {'order_id': order_id, 'delivery_person_id': dp.id}

        except Exception as e:
            logger.error(f"Error assigning delivery person to order {order_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Transaction will be automatically rolled back if commit() wasn't called
            raise
    
    @staticmethod
    @db_session
    def get_random_delivery_person() -> Optional[DeliveryPerson]:
        """Get a random delivery person from all delivery persons in the database.
        
        Returns:
            A random delivery person if any exist, None otherwise
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Getting random delivery person")
        all_delivery_persons = list(DeliveryPerson.select()[:])
        logger.info(f"Found {len(all_delivery_persons)} total delivery persons")
        if not all_delivery_persons:
            logger.info("No delivery persons found")
            return None
        selected = random.choice(all_delivery_persons)
        logger.info(f"Selected random delivery person: {selected.username}")
        return selected
    
    @staticmethod
    def create_multiple_pizza_order(
        user_id: int,
        pizza_quantities: List[List[int]],
        extra_ids: Optional[List[int]] = None,
        discount_code: Optional[str] = None,
        postal_code: Optional[str] = None
    ) -> Order:
        """Create a new order with multiple pizzas, validating stock and automatically assigning delivery person.
        
        Args:
            user_id: ID of the user placing the order
            pizza_quantities: List of [pizza_id, quantity] pairs
            extra_ids: Optional list of extra IDs to include
            discount_code: Optional discount code to apply
            postal_code: Optional postal code for delivery
            
        Returns:
            The created Order object
            
        Raises:
            ValueError: If user not found, insufficient stock, or invalid pizza IDs
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Validate user exists
        user = User.get(id=user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")
        
        # Determine postal code
        final_postal_code = postal_code or user.postalCode
        if not final_postal_code:
            raise ValueError("Postal code must be provided or set on the user")
        
        if not pizza_quantities:
            raise ValueError("At least one pizza is required")
        
        # Collect all pizza IDs for batch fetching
        pizza_ids = [item[0] for item in pizza_quantities]
        
        # Fetch all pizzas in a single query
        pizzas = list(Pizza.select(lambda p: p.id in pizza_ids)) if pizza_ids else []
        
        # Create dictionary for O(1) lookups
        pizza_dict = {p.id: p for p in list(pizzas)}
        
        # Validate all pizzas exist and check stock
        for item in pizza_quantities:
            pizza_id, quantity = item
            pizza = pizza_dict.get(pizza_id)
            if not pizza:
                raise ValueError(f"Pizza with id {pizza_id} not found")
            
            if quantity <= 0:
                raise ValueError(f"Quantity for pizza {pizza_id} must be positive")
            
            if pizza.stock < quantity:
                raise ValueError(f"Insufficient stock for pizza '{pizza.name}'. Available: {pizza.stock}, Requested: {quantity}")
        
        # Find available delivery person or get random one
        delivery_person = None
        available_dps = QueryManager.get_available_delivery_persons()
        
        if available_dps:
            delivery_person = available_dps[0]
            logger.info(f"Assigned available delivery person: {delivery_person.username}")
        else:
            delivery_person = QueryManager.get_random_delivery_person()
            if delivery_person:
                logger.info(f"No available delivery persons, randomly assigned: {delivery_person.username}")
            else:
                logger.warning("No delivery persons available in the system")
        
        # Create the order
        order = Order(
            user=user,
            status=OrderStatus.Pending,
            postalCode=final_postal_code,
            created_at=datetime.now(),
            delivery_person=delivery_person
        )
        
        # Add pizzas with quantities and update stock
        for item in pizza_quantities:
            pizza_id, quantity = item
            pizza = pizza_dict.get(pizza_id)
            
            # Create the pizza relation
            OrderPizzaRelation(order=order, pizza=pizza, quantity=quantity)
            
            # Update stock
            pizza.stock -= quantity
            logger.info(f"Updated stock for pizza '{pizza.name}': {pizza.stock + quantity} -> {pizza.stock}")
        
        # Add extras if provided
        if extra_ids:
            extra_ids_set = set(extra_ids)
            extras = list(Extra.select(lambda e: e.id in extra_ids_set)) if extra_ids_set else []
            extra_dict = {e.id: e for e in list(extras)}
            
            for extra_id in extra_ids:
                extra = extra_dict.get(extra_id)
                if not extra:
                    raise ValueError(f"Extra with id {extra_id} not found")
                order.extras.add(extra)
        
        # Update delivery person status if they were available
        if delivery_person and delivery_person.status == DeliveryStatus.Available:
            delivery_person.status = DeliveryStatus.On_Delivery
            logger.info(f"Updated delivery person {delivery_person.username} status to On_Delivery")
        
        # Apply discount code if provided
        if discount_code:
            logger.info(f"Processing discount code: {discount_code}")
            # Get discount code details using existing query
            dc_details = QueryManager.get_discount_code_details(discount_code)
            
            if not dc_details or not dc_details.get('is_valid'):
                raise ValueError(f"Invalid or expired discount code: {discount_code}")
            
            dc = DiscountCode.get(code=discount_code)
            if not dc:
                raise ValueError(f"Discount code not found: {discount_code}")
            
            # Associate discount code with user
            user.discount_code = dc
            
            # Mark discount code as used if it's a one-time use
            if dc.percentage == 0.0:  # Birthday codes are one-time use
                dc.used = True
                dc.used_by = user
                logger.info(f"Marked birthday discount code {discount_code} as used by user {user.username}")
        
        commit()
        return order
    
    # Optional: List undelivered or delayed orders
 
# -=-=-=-=-=- STAFF QUERIES -=-=-=-=-=- #
    # Add/remove staff order (if they are able to order pizza)
    # (OPTIONAL: Create earnings report, filtered by Driver workload, ingredients usage and costing)
    
# Sum of earnings:
    @staticmethod
    @db_session
    def get_earnings_by_gender(gender: str) -> float:
        """Get total earnings (salaries) for employees filtered by gender."""
        return sum(e.salary for e in list(Employee.select()[:]) if e.Gender == gender)

    @staticmethod
    @db_session
    def get_earnings_by_age_group(min_age: int, max_age: int) -> float:
        """Get total earnings (salaries) for employees filtered by age group."""
        today = date.today()
        return float(sum(e.salary for e in list(Employee.select()[:])
                   if e.birthdate and (today.year - e.birthdate.year) >= min_age
                   and (today.year - e.birthdate.year) <= max_age))

    @staticmethod
    @db_session
    def get_earnings_by_postal_code(postal_code: str) -> float:
        """Get total earnings (salaries) for employees filtered by postal code."""
        return sum(e.salary for e in list(Employee.select()[:]) if e.postalCode == postal_code)

# Average of earnings:
    @staticmethod
    @db_session
    def get_average_salary_by_gender(gender: str) -> float:
        """Get average salary for employees filtered by gender."""
        # Get all employees and calculate average in Python due to Pony ORM limitations
        employees = list(Employee.select()[:])
        filtered_employees = [e for e in employees if e.Gender == gender]
        if not filtered_employees:
            return 0.0
        return sum(e.salary for e in filtered_employees) / len(filtered_employees)

    @staticmethod
    @db_session
    def get_average_salary_by_age_group(min_age: int, max_age: int) -> float:
        """Get average salary for employees filtered by age group."""
        today = date.today()
        # Get all employees and calculate average in Python due to Pony ORM limitations
        employees = list(Employee.select())
        filtered_employees = []
        for e in employees:
            if e.birthdate:
                age = today.year - e.birthdate.year
                if min_age <= age <= max_age:
                    filtered_employees.append(e)
        if not filtered_employees:
            return 0.0
        return sum(e.salary for e in filtered_employees) / len(filtered_employees)

    @staticmethod
    @db_session
    def get_average_salary_by_postal_code(postal_code: str) -> float:
        """Get average salary for employees filtered by postal code."""
        # Get all employees and calculate average in Python due to Pony ORM limitations
        employees = list(Employee.select()[:])
        filtered_employees = [e for e in employees if e.postalCode == postal_code]
        if not filtered_employees:
            return 0.0
        return sum(e.salary for e in filtered_employees) / len(filtered_employees)


# -=-=-=-=-=- REPORT QUERIES -=-=-=-=-=- #

    @staticmethod
    @db_session
    def get_undelivered_customer_orders() -> List[Order]:
        """Get all undelivered orders placed by customers."""
        # Get all orders and filter in Python due to Pony ORM limitations
        all_orders = list(Order.select())
        customer_orders = []
        for o in all_orders:
            if isinstance(o.user, Customer) and o.status in [OrderStatus.Pending, OrderStatus.In_Progress]:
                customer_orders.append(o)
        return customer_orders

    @staticmethod
    @db_session
    def get_undelivered_staff_orders() -> List[Order]:
        """Get all undelivered orders placed by staff (employees)."""
        # Get all orders and filter in Python due to Pony ORM limitations
        all_orders = list(Order.select())
        staff_orders = []
        for o in all_orders:
            if isinstance(o.user, Employee) and o.status in [OrderStatus.Pending, OrderStatus.In_Progress]:
                staff_orders.append(o)
        return staff_orders
    
    @staticmethod
    @db_session
    def get_top_3_pizzas_past_month() -> List[Dict[str, Any]]:
        """Get the top 3 pizzas sold in the past month by quantity."""
        past_month = datetime.now() - timedelta(days=30)
        # Get all orders in the past month and aggregate pizza quantities
        all_orders = list(Order.select(lambda o: o.created_at >= past_month))
        pizza_sales = {}
        
        for order in all_orders:
            for opr in order.pizza_relations:
                pizza_id = opr.pizza.id
                if pizza_id not in pizza_sales:
                    pizza_sales[pizza_id] = {'pizza': opr.pizza, 'quantity': 0}
                pizza_sales[pizza_id]['quantity'] += opr.quantity
        
        # Sort by quantity and get top 3
        sorted_pizzas = sorted(pizza_sales.values(), key=lambda x: x['quantity'], reverse=True)[:3]
        return [{'pizza': item['pizza'], 'total_quantity': item['quantity']} for item in sorted_pizzas]
