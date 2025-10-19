from datetime import datetime, date, time
from enum import Enum
from pony.orm import Required, PrimaryKey, Optional as PonyOptional, Set, db_session, commit
from .db import db

import re
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import secrets
import base64


class IngredientType(str, Enum):
    Vegan = "Vegan"
    Vegetarian = "Vegetarian"
    Normal = "Normal"

class ExtraType(str, Enum):
    Drink = "Drink"
    Dessert = "Dessert"

class DeliveryStatus(str, Enum):
    Available = "Available"
    On_Delivery = "On Delivery"
    Off_Duty = "Off Duty"

class OrderStatus(str, Enum):
    Pending = "Pending"
    In_Progress = "In Progress"
    Delivered = "Delivered"
    Cancelled = "Cancelled"

class OrderPizzaRelation(db.Entity):
    order = Required("Order")
    pizza = Required("Pizza")
    quantity = Required(int, default=1)
    PrimaryKey(order, pizza)

class Pizza(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    ingredients = Set("Ingredient")
    order_relations = Set(OrderPizzaRelation)
    description = PonyOptional(str)
    stock = Required(int, default=1)


class Extra(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    price = Required(float)
    order = Set("Order")
    type = Required(py_type=ExtraType, sql_type='VARCHAR')


class Ingredient(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    price = Required(float)
    type = Required(py_type=IngredientType, sql_type='VARCHAR')
    pizza = Set("Pizza")


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    username = Required(str, unique=True)
    email = Required(str, unique=True)
    birthdate = PonyOptional(date)
    address = Required(str)
    postalCode = Required(str)
    phone = Required(str)
    orders = Set("Order")
    discount_code = PonyOptional("DiscountCode")
    Gender = Required(str)
    password_hash = Required(str)
    salt = Required(str)  # Store the unique salt for each user

    @staticmethod
    def _get_pepper():
        return os.getenv("PASSWORD_PEPPER", "default_pepper_change_in_production")

    @staticmethod
    def hash_password(password: str) -> tuple[str, str]:
     
        salt = secrets.token_bytes(32)
        salt_b64 = base64.b64encode(salt).decode('utf-8')
        pepper = User._get_pepper()
        password_with_pepper = password + pepper

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=1000,
            backend=default_backend()
        )
        key = kdf.derive(password_with_pepper.encode('utf-8'))
        hashed_password = base64.b64encode(key).decode('utf-8')

        return hashed_password, salt_b64

    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: str) -> bool:
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.debug("Starting password verification")
            salt_bytes = base64.b64decode(salt)
            logger.debug(f"Salt decoded successfully, length: {len(salt_bytes)}")

            pepper = User._get_pepper()
            password_with_pepper = password + pepper
            logger.debug(f"Pepper applied: {pepper[:5]}...")

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt_bytes,
                iterations=1000,
                backend=default_backend()
            )
            key = kdf.derive(password_with_pepper.encode('utf-8'))
            derived_hash = base64.b64encode(key).decode('utf-8')
            logger.debug(f"Derived hash generated, comparing with stored hash")

            result = secrets.compare_digest(derived_hash, hashed_password)
            logger.debug(f"Password verification result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in verify_password: {str(e)}")
            return False

    def set_password(self, password: str):
        hashed_password, salt = User.hash_password(password)
        self.password_hash = hashed_password
        self.salt = salt

    def check_password(self, password: str) -> bool:
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Checking password for user {self.username}")
            result = User.verify_password(password, self.password_hash, self.salt)
            logger.debug(f"Password check result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in check_password: {str(e)}")
            raise
    
    def validate_phone(self):
        if self.phone:
            clean = re.sub(r'[^\d+]', '', self.phone)
            if clean.startswith('+'):
                if not re.match(r'^\+[1-9][0-9]{6,14}$', clean):
                    raise ValueError("Invalid international phone format")
            else:
                if not re.match(r'^[0-9]{10}$', clean):
                    raise ValueError("Domestic phone must be exactly 10 digits")
    
    @staticmethod
    @db_session
    def create_full_user(username: str, email: str, password: str, address: str, postalCode: str,
                        phone: str, Gender: str, user_type: str = "customer",
                        birthdate: date | None = None, position: str | None = None,
                        salary: float | None = None, loyalty_points: int = 0,
                        birthday_order: bool = False, status: DeliveryStatus = DeliveryStatus.Available):
        """Create a complete user of any type with all required fields in one operation."""
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Creating {user_type} user: {username}")
            
            # Validate required fields
            if not username or not email or not password or not address or not postalCode or not phone or not Gender:
                raise ValueError("All required fields must be provided")
            
            # Hash the password securely during creation
            hashed_password, salt = User.hash_password(password)
            
            # Create base user data
            user_data = {
                'username': username,
                'email': email,
                'password_hash': hashed_password,
                'salt': salt,
                'address': address,
                'postalCode': postalCode,
                'phone': phone,
                'Gender': Gender,
                'birthdate': birthdate
            }
            logger.debug(f"Base user data created: {user_data}")
            
            # Create user based on type
            if user_type == "customer":
                customer_data = {
                    **user_data,
                    'loyalty_points': loyalty_points,
                    'birthday_order': birthday_order
                }
                user = Customer(**customer_data)
            elif user_type == "employee":
                if not position or not salary:
                    raise ValueError("Position and salary are required for employee accounts")
                employee_data = {
                    **user_data,
                    'position': position,
                    'salary': salary
                }
                user = Employee(**employee_data)
            elif user_type == "delivery_person":
                if not position or not salary:
                    raise ValueError("Position and salary are required for delivery person accounts")
                delivery_person_data = {
                    **user_data,
                    'position': position,
                    'salary': salary,
                    'status': DeliveryStatus.Available
                }
                user = DeliveryPerson(**delivery_person_data)
            else:
                raise ValueError(f"Invalid user type: {user_type}. Must be 'customer', 'employee', or 'delivery_person'")
            
            # Commit the transaction to ensure the user ID is populated
            commit()
            logger.debug(f"User created successfully with ID: {user.id}")
            
            return user
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e



class Customer(User):
    loyalty_points = Required(int, default=0)
    birthday_order = Required(bool, default=False)

class Employee(User):
    position = Required(str)
    salary = Required(float)

class DeliveryPerson(Employee):
    status = Required(py_type=DeliveryStatus, sql_type='VARCHAR')
    delivered_orders = Set("Order")

class Order(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    pizza_relations = Set("OrderPizzaRelation")
    extras = Set(Extra)
    status = Required(py_type=OrderStatus, sql_type='VARCHAR')
    created_at = Required(datetime, default=datetime.now)
    delivered_at = PonyOptional(datetime)
    delivery_person = PonyOptional(DeliveryPerson)
    postalCode = Required(str)

class DiscountCode(db.Entity):
    code = PrimaryKey(str)
    percentage = Required(float) # If percentage is 0.0, then its a birthday code. This would mean that you get 1 free pizza (cheapest) and 1 free drink
    valid_until = Required(datetime)
    valid_from = PonyOptional(datetime)
    used = Required(bool, default=False)
    used_by = PonyOptional(User)
