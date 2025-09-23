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

# -=-=-=-=-=- BASIC MENU QUERIES -=-=-=-=-=- #
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

# -=-=-=-=-=- USER QUERIES -=-=-=-=-=- #
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
        """Create a new order with at least one pizza and optional extras, by user ID, with optional discount code and additional order details.
        pizza_quantities should be a list of [pizza_id, quantity] pairs.
        """
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

        if not pizza_quantities:
            raise ValueError("At least one pizza is required")

        # Collect all pizza and extra IDs for batch fetching
        pizza_ids = [item[0] for item in pizza_quantities]
        extra_ids_set = set(extra_ids) if extra_ids else set()

        # Fetch all pizzas and extras in single queries
        pizzas = Pizza.select(p for p in Pizza if p.id in pizza_ids) if pizza_ids else []
        extras = Extra.select(e for e in Extra if e.id in extra_ids_set) if extra_ids_set else []

        # Create dictionaries for O(1) lookups
        pizza_dict = {p.id: p for p in pizzas}
        extra_dict = {e.id: e for e in extras}

        # Create the order
        order = Order(
            user=user,
            status=status,
            postalCode=final_postal_code,
            created_at=final_created_at,
            delivered_at=delivered_at,
            delivery_person=delivery_person
        )

        # Add pizzas with quantities using dictionary lookup
        for item in pizza_quantities:
            pizza_id, quantity = item
            pizza = pizza_dict.get(pizza_id)
            if not pizza:
                raise ValueError(f"Pizza with id {pizza_id} not found")
            OrderPizzaRelation(order=order, pizza=pizza, quantity=quantity)

        # Add extras if provided using dictionary lookup
        if extra_ids:
            for extra_id in extra_ids:
                extra = extra_dict.get(extra_id)
                if not extra:
                    raise ValueError(f"Extra with id {extra_id} not found")
                order.extras.add(extra)

        # Handle discount code if provided
        if discount_code:
            dc = DiscountCode.get(code=discount_code)
            if not dc:
                raise ValueError(f"Discount code '{discount_code}' not found")
            now = datetime.now()
            if dc.used:
                raise ValueError("Discount code has already been used")
            if dc.valid_from and now < dc.valid_from:
                raise ValueError("Discount code is not yet valid")
            if now > dc.valid_until:
                raise ValueError("Discount code has expired")
            dc.used = True
            dc.used_by = user
            # Optionally assign to user if not already set
            if not user.discount_code:
                user.discount_code = dc

        return order

    @staticmethod
    @db_session
    def update_order(order_id: int, 
                     status: Optional[OrderStatus] = None, 
                     delivered_at: Optional[datetime] = None, 
                     delivery_person_id: Optional[int] = None, 
                     postal_code: Optional[str] = None
                     ) -> Order:
        """Update an existing order's details such as status, delivery time, delivery person, or postal code."""
        order = Order.get(id=order_id)
        if not order:
            raise ValueError(f"Order with id {order_id} not found")

        if status is not None:
            order.status = status
            # Automatically set delivered_at if status is Delivered and not set
            if status == OrderStatus.Delivered and order.delivered_at is None:
                order.delivered_at = datetime.now()

        if delivered_at is not None:
            order.delivered_at = delivered_at

        if delivery_person_id is not None:
            delivery_person = DeliveryPerson.get(id=delivery_person_id)
            if not delivery_person:
                raise ValueError(f"Delivery person with id {delivery_person_id} not found")
            order.delivery_person = delivery_person

        if postal_code is not None:
            order.postalCode = postal_code

        return order
    
    @staticmethod
    @db_session
    def delete_order(order_id: int) -> bool:
        """Delete an order from the database by order ID."""
        order = Order.get(id=order_id)
        if not order:
            return False
        order.delete()
        return True
    
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
        for opr in order.Pizzas:
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
        for extra in order.extras:
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
            discount_amount = total * (dc.percentage / 100)
            total -= discount_amount
            discount_info = {
                'code': dc.code,
                'percentage': dc.percentage,
                'amount': round(discount_amount, 2)
            }

        return {
            'total_price': round(total, 2),
            'items': items,
            'discount': discount_info
        }

    @staticmethod
    @db_session
    def count_extras_by_type(extra_type: ExtraType) -> int:
        """Example: Count extras by type."""
        return Extra.select(e for e in Extra if e.type == extra_type).count()

# -=-=-=-=-=- LOYALTY QUERIES -=-=-=-=-=- #
    # Count pizzas bought for eligibility
    # Apply DiscountCode
    # Birthday benefit

# -=-=-=-=-=- DELIVERY QUERIES -=-=-=-=-=- #

    @staticmethod
    @db_session
    def get_available_delivery_persons() -> List[DeliveryPerson]:
        """Get all delivery persons who are currently available for assignments."""
        return DeliveryPerson.select(dp for dp in DeliveryPerson if dp.status == DeliveryStatus.Available)[:]
        
    @staticmethod
    @db_session
    def update_delivery_person_status(delivery_person_id: int, new_status: DeliveryStatus) -> DeliveryPerson:
        """Update the status of a delivery person."""
        dp = DeliveryPerson.get(id=delivery_person_id)
        if not dp:
            raise ValueError(f"Delivery person with id {delivery_person_id} not found")
        dp.status = new_status
        return dp
    
    @staticmethod
    @db_session
    def assign_delivery_person_to_order(order_id: int) -> Optional[Dict[str, Any]]:
        """Assign an available delivery person to an order.
        Returns a dict with order_id and delivery_person_id if assignment was successful,
        None if no suitable delivery person found."""
        order = Order.get(id=order_id)
        if not order:
            raise ValueError(f"Order with id {order_id} not found")
        if order.delivery_person:
            raise ValueError("Order already has a delivery person assigned")
        if order.status != OrderStatus.In_Progress:
            raise ValueError("Order must be in progress to assign delivery person")

        # Find available delivery persons using the dedicated query
        available_dps = QueryManager.get_available_delivery_persons()
        if not available_dps:
            return None  # No available delivery person

        # Assign the first available delivery person
        dp = available_dps[0]
        order.delivery_person = dp
        dp.status = DeliveryStatus.On_Delivery
        return {'order_id': order_id, 'delivery_person_id': dp.id}
    
    # Optional: List undelivered or delayed orders
 
# -=-=-=-=-=- STAFF QUERIES -=-=-=-=-=- #
    # Add/remove staff order (if they are able to order pizza)
    # Create earnings report, filtered by:
        # Gender
        # Age group
        # Postal code
        # (optional: Driver workload, ingredients usage and costing)

# -=-=-=-=-=- REPORT QUERIES -=-=-=-=-=- #
    # Undelivered orders (customer / staff)
    # Create report of top 3 pizza's sold in the past month
