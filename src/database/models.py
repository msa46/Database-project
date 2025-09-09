from datetime import datetime, date, time
from enum import Enum
from pony.orm import Required, PrimaryKey, Optional, Set
from db import db

import re


def validate_phone(phone):
    clean = re.sub(r'[^\d+]', '', phone)
    if clean.startswith('+'):
        if not re.match(r'^\+[1-9][0-9]{6,14}$', clean):
            raise ValueError("Invalid international phone format")
    else:
        if not re.match(r'^[0-9]{10}$', clean):
            raise ValueError("Domestic phone must be exactly 10 digits")
    
    return phone

class IngredientType(Enum):
    Vegan = "Vegan"
    Vegetarian = "Vegetarian"
    Normal = "Normal"

class ExtraType(Enum):
    Drink = "Drink"
    Dessert = "Dessert"

class DeliveryStatus(Enum):
    Available = "Available"
    On_Delivery = "On Delivery"
    Off_Duty = "Off Duty"

class OrderStatus(Enum):
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
    type = Required(ExtraType, py_type=ExtraType)


class Ingredient(db.Entity):
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    price = Required(float)
    type = Required(IngredientType, py_type=IngredientType)
    pizza = set(Pizza)


class User(db.Entity):
    id = PrimaryKey(int, auto=True)
    username = Required(str, unique=True)
    email = Required(str, unique=True)
    birthdate = Optional(date)
    address = Optional(str)
    postalCode = Optional(str)
    phone = Optional(str, py_check=lambda x: validate_phone(x))
    orders = Set("Order")
    Gender = Optional(str)



class Customer(User):
    loyalty_points = Required(int, default=0)
    birthday_order = Required(bool)
class Employee(User):
    position = Required(str)  
    salary = Required(float)

class DeliveryPerson(Employee):
    status = Required(DeliveryStatus, py_type=DeliveryStatus) 
    orders = Set("Order")

class Order(db.Entity):
    id = PrimaryKey(int, auto=True)
    user = Required(User)
    Pizzas = Set("OrderPizzaRelation")
    extras = Set(Extra)
    status = Required(OrderStatus, py_type=OrderStatus)
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
    # users = Set(User)