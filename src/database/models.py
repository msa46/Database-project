from datetime import datetime, date, time
from enum import Enum
from pony.orm import Required, PrimaryKey, Optional, Set, db_session
from .db import db

import re


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
    order = Set(OrderPizzaRelation)
    description = Optional(str)


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
    birthdate = Optional(date)
    address = Optional(str)
    postalCode = Optional(str)
    phone = Optional(str)
    orders = Set("Order")
    discount_code = Optional("DiscountCode")
    Gender = Optional(str)
    
    def validate_phone(self):
        if self.phone:
            clean = re.sub(r'[^\d+]', '', self.phone)
            if clean.startswith('+'):
                if not re.match(r'^\+[1-9][0-9]{6,14}$', clean):
                    raise ValueError("Invalid international phone format")
            else:
                if not re.match(r'^[0-9]{10}$', clean):
                    raise ValueError("Domestic phone must be exactly 10 digits")



class Customer(User):
    loyalty_points = Required(int, default=0)
    birthday_order = Required(bool)
class Employee(User):
    position = Required(str)  
    salary = Required(float)

class DeliveryPerson(Employee):
    status = Required(py_type=DeliveryStatus, sql_type='VARCHAR') 
    delivered_orders = Set("Order")

class Order(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    Pizzas = Set("OrderPizzaRelation")
    extras = Set(Extra)
    status = Required(py_type=OrderStatus, sql_type='VARCHAR')
    created_at = Required(datetime, default=datetime.now)
    delivered_at = Optional(datetime)
    delivery_person = Optional(DeliveryPerson)
    postalCode = Required(str)

class DiscountCode(db.Entity):
    code = PrimaryKey(str)
    percentage = Required(float)
    valid_until = Required(datetime)
    valid_from = Optional(datetime)
    used = Required(bool, default=False)
    used_by = Optional(User)
