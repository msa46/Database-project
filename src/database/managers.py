from datetime import datetime, date, time
from typing import List, Dict, Any, Optional, Union
from pony.orm import db_session, commit
import random
from faker import Faker

from .models import (
    IngredientType, ExtraType, DeliveryStatus, OrderStatus,
    OrderPizzaRelation, Pizza, Extra, Ingredient, User,
    Customer, Employee, DeliveryPerson, Order, DiscountCode
)
from .db import db


class BaseManager:
    """Common functionality for entity managers."""
    
    @staticmethod
    @db_session
    def create_entity(entity_class, **kwargs):
        return entity_class(**kwargs)
    
    @staticmethod
    @db_session
    def create_entities_batch(entity_class, entities_data: List[Dict[str, Any]]):
        entities = []
        for entity_data in entities_data:
            entity = entity_class(**entity_data)
            entities.append(entity)
        return entities


class IngredientManager(BaseManager):
    """Handles ingredient creation."""
    
    @staticmethod
    def create(name: str, price: float, type: IngredientType) -> Ingredient:
        return BaseManager.create_entity(Ingredient, name=name, price=price, type=type)
    
    @staticmethod
    def create_batch(ingredients_data: List[Dict[str, Any]]) -> List[Ingredient]:
        return BaseManager.create_entities_batch(Ingredient, ingredients_data)


class ExtraManager(BaseManager):
    """Handles extra items creation."""
    
    @staticmethod
    def create(name: str, price: float, type: ExtraType) -> Extra:
        return BaseManager.create_entity(Extra, name=name, price=price, type=type)
    
    @staticmethod
    def create_batch(extras_data: List[Dict[str, Any]]) -> List[Extra]:
        return BaseManager.create_entities_batch(Extra, extras_data)


class PizzaManager(BaseManager):
    """Handles pizza creation."""
    
    @staticmethod
    def create(name: str, description: Optional[str] = None, ingredients: Optional[List[Ingredient]] = None) -> Pizza:
        return BaseManager.create_entity(Pizza, name=name, description=description, ingredients=ingredients or [])
    
    @staticmethod
    def create_batch(pizzas_data: List[Dict[str, Any]]) -> List[Pizza]:
        return BaseManager.create_entities_batch(Pizza, pizzas_data)


class UserManager(BaseManager):
    """Handles user creation."""

    @staticmethod
    def create(username: str, email: str, password: str, birthdate: Optional[date] = None,
              address: Optional[str] = None, postalCode: Optional[str] = None,
              phone: Optional[str] = None, Gender: Optional[str] = None) -> User:
        # Create user without password first
        user = BaseManager.create_entity(
            User,
            username=username,
            email=email,
            birthdate=birthdate,
            address=address,
            postalCode=postalCode,
            phone=phone,
            Gender=Gender,
            password_hash="",  # Temporary value, will be set properly
            salt=""  # Temporary value, will be set properly
        )

        # Set the password using the secure hashing method
        user.set_password(password)

        return user
    
    @staticmethod
    def create_batch(users_data: List[Dict[str, Any]]) -> List[User]:
        return BaseManager.create_entities_batch(User, users_data)


class CustomerManager(UserManager):
    """Handles customer creation."""

    @staticmethod
    def create(username: str, email: str, password: str, loyalty_points: int = 0,
              birthday_order: bool = False, **kwargs) -> Customer:
        # Generate a temporary password hash and salt
        temp_password = "temp_password_" + username
        temp_hash, temp_salt = User.hash_password(temp_password)
        
        # Create customer with temporary password hash
        customer_data = {
            'username': username,
            'email': email,
            'password_hash': temp_hash,
            'salt': temp_salt,
            'loyalty_points': loyalty_points,
            'birthday_order': birthday_order,
            **kwargs
        }
        
        customer = BaseManager.create_entity(Customer, **customer_data)

        # Set the password using the secure hashing method
        customer.set_password(password)

        return customer
    
    @staticmethod
    def create_batch(customers_data: List[Dict[str, Any]]) -> List[Customer]:
        return BaseManager.create_entities_batch(Customer, customers_data)


class EmployeeManager(UserManager):
    """Handles employee creation."""

    @staticmethod
    def create(username: str, email: str, password: str, position: str, salary: float, **kwargs) -> Employee:
        # Generate a temporary password hash and salt
        temp_password = "temp_password_" + username
        temp_hash, temp_salt = User.hash_password(temp_password)
        
        # Create employee with temporary password hash
        user_data = {
            'username': username,
            'email': email,
            'password_hash': temp_hash,
            'salt': temp_salt,
            **kwargs
        }
        employee_data = {
            'position': position,
            'salary': salary
        }
        
        employee = BaseManager.create_entity(Employee, **user_data, **employee_data)
        
        # Set the password using the secure hashing method
        employee.set_password(password)
        
        return employee
    
    @staticmethod
    def create_batch(employees_data: List[Dict[str, Any]]) -> List[Employee]:
        return BaseManager.create_entities_batch(Employee, employees_data)


class DeliveryPersonManager(EmployeeManager):
    """Handles delivery person creation."""

    @staticmethod
    def create(username: str, email: str, password: str, position: str, salary: float,
              status: DeliveryStatus = DeliveryStatus.Available, **kwargs) -> DeliveryPerson:
        # Generate a temporary password hash and salt
        temp_password = "temp_password_" + username
        temp_hash, temp_salt = User.hash_password(temp_password)
        
        # Create delivery person with temporary password hash
        employee_data = {
            'username': username,
            'email': email,
            'password_hash': temp_hash,
            'salt': temp_salt,
            'position': position,
            'salary': salary,
            **kwargs
        }
        delivery_person_data = {
            'status': status
        }
        
        delivery_person = BaseManager.create_entity(DeliveryPerson, **employee_data, **delivery_person_data)
        
        # Set the password using the secure hashing method
        delivery_person.set_password(password)
        
        return delivery_person
    
    @staticmethod
    def create_batch(delivery_persons_data: List[Dict[str, Any]]) -> List[DeliveryPerson]:
        return BaseManager.create_entities_batch(DeliveryPerson, delivery_persons_data)


class OrderManager(BaseManager):
    """Handles order creation."""
    
    @staticmethod
    def create(user: User, status: OrderStatus = OrderStatus.Pending, 
              pizzas: Optional[List[Dict[str, Any]]] = None,
              extras: Optional[List[Extra]] = None,
              delivery_person: Optional[DeliveryPerson] = None,
              postalCode: Optional[str] = None) -> Order:
        order_data = {
            'user': user,
            'status': status,
            'postalCode': postalCode or user.postalCode or "0000AA"
        }
        
        if delivery_person:
            order_data['delivery_person'] = delivery_person
            
        order = BaseManager.create_entity(Order, **order_data)
        
        if pizzas:
            for pizza_data in pizzas:
                pizza = pizza_data['pizza']
                quantity = pizza_data.get('quantity', 1)
                OrderPizzaRelation(order=order, pizza=pizza, quantity=quantity)
        
        if extras:
            for extra in extras:
                order.extras.add(extra)
                
        return order
    
    @staticmethod
    def create_batch(orders_data: List[Dict[str, Any]]) -> List[Order]:
        orders = []
        for order_data in orders_data:
            user = order_data.pop('user')
            pizzas = order_data.pop('pizzas', None)
            extras = order_data.pop('extras', None)
            delivery_person = order_data.pop('delivery_person', None)
            
            order = OrderManager.create(
                user=user,
                pizzas=pizzas,
                extras=extras,
                delivery_person=delivery_person,
                **order_data
            )
            orders.append(order)
        return orders


class DiscountCodeManager(BaseManager):
    """Handles discount code creation."""
    
    @staticmethod
    def create(code: str, percentage: float, valid_until: datetime, 
              valid_from: Optional[datetime] = None, 
              used: bool = False, used_by: Optional[User] = None) -> DiscountCode:
        return BaseManager.create_entity(
            DiscountCode,
            code=code,
            percentage=percentage,
            valid_until=valid_until,
            valid_from=valid_from,
            used=used,
            used_by=used_by
        )
    
    @staticmethod
    def create_batch(discount_codes_data: List[Dict[str, Any]]) -> List[DiscountCode]:
        return BaseManager.create_entities_batch(DiscountCode, discount_codes_data)


class DataManager:
    """Main data manager for creating test data."""
    
    def __init__(self):
        self.ingredient = IngredientManager()
        self.extra = ExtraManager()
        self.pizza = PizzaManager()
        self.user = UserManager()
        self.customer = CustomerManager()
        self.employee = EmployeeManager()
        self.delivery_person = DeliveryPersonManager()
        self.order = OrderManager()
        self.discount_code = DiscountCodeManager()
        self.faker = Faker()
    
    @db_session
    def create_fake_ingredients(self, count=5):
        ingredient_names = [
            'Tomato Sauce', 'Mozzarella', 'Pepperoni', 'Mushrooms', 'Basil',
            'Olives', 'Ham', 'Pineapple', 'Onions', 'Bell Peppers',
            'Chicken', 'Bacon', 'Tomatoes', 'Oregano', 'Garlic'
        ]
        
        ingredients_data = []
        for _ in range(count):
            name = random.choice(ingredient_names)
            price = round(random.uniform(0.3, 2.0), 2)
            ingredient_type = random.choice(list(IngredientType))
            ingredients_data.append({'name': name, 'price': price, 'type': ingredient_type})
        
        return self.ingredient.create_batch(ingredients_data)
    
    @db_session
    def create_fake_extras(self, count=4):
        drink_names = ['Coca Cola', 'Sprite', 'Fanta', 'Water', 'Orange Juice', 'Iced Tea']
        dessert_names = ['Ice Cream', 'Tiramisu', 'Cheesecake', 'Chocolate Cake', 'Apple Pie']
        
        extras_data = []
        for _ in range(count):
            if random.choice([True, False]):
                name = random.choice(drink_names)
                extra_type = ExtraType.Drink
            else:
                name = random.choice(dessert_names)
                extra_type = ExtraType.Dessert
            
            price = round(random.uniform(1.5, 5.0), 2)
            extras_data.append({'name': name, 'price': price, 'type': extra_type})
        
        return self.extra.create_batch(extras_data)
    
    @db_session
    def create_fake_pizzas(self, count=3, ingredients=None):
        if ingredients is None:
            ingredients = self.create_fake_ingredients(10)
        
        pizza_names = ['Margherita', 'Pepperoni', 'Hawaiian', 'Vegan Special', 'Veggie Delight',
                      'BBQ Chicken', 'Meat Lovers', 'Four Cheese', 'Seafood', 'Spicy Pepperoni']
        
        pizzas = []
        for _ in range(count):
            name = random.choice(pizza_names)
            description = f"Delicious {name.lower()} pizza with fresh ingredients"
            
            pizza_ingredients = random.sample(ingredients, random.randint(2, min(5, len(ingredients))))
            
            pizza = self.pizza.create(name=name, description=description, ingredients=pizza_ingredients)
            pizzas.append(pizza)
        
        return pizzas
    
    @db_session
    def create_fake_customers(self, count=2):
        customers = []
        for _ in range(count):
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()
            username = f"{first_name.lower()}_{last_name.lower()}"
            email = f"{username}@{self.faker.free_email_domain()}"
            password = self.faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)

            birthdate = self.faker.date_of_birth(minimum_age=18, maximum_age=70)
            address = self.faker.street_address()
            postal_code = self.faker.postcode()
            phone = self.faker.phone_number()
            gender = random.choice(['Male', 'Female', 'Other'])
            loyalty_points = random.randint(0, 500)
            birthday_order = random.choice([True, False])

            customer = self.customer.create(
                username=username,
                email=email,
                password=password,
                birthdate=birthdate,
                address=address,
                postalCode=postal_code,
                phone=phone,
                Gender=gender,
                loyalty_points=loyalty_points,
                birthday_order=birthday_order
            )
            customers.append(customer)

        return customers
    
    @db_session
    def create_fake_delivery_persons(self, count=1):
        positions = ['Delivery Driver', 'Senior Delivery Driver', 'Delivery Manager']
        statuses = list(DeliveryStatus)

        delivery_persons = []
        for _ in range(count):
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()
            username = f"delivery_{first_name.lower()}"
            email = f"{username}@{self.faker.free_email_domain()}"
            password = self.faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)

            position = random.choice(positions)
            salary = round(random.uniform(1800.0, 2500.0), 2)
            status = random.choice(statuses)
            phone = self.faker.phone_number()
            gender = random.choice(['Male', 'Female', 'Other'])

            delivery_person = self.delivery_person.create(
                username=username,
                email=email,
                password=password,
                position=position,
                salary=salary,
                status=status,
                phone=phone,
                Gender=gender
            )
            delivery_persons.append(delivery_person)

        return delivery_persons
    
    @db_session
    def create_fake_orders(self, count=2, customers=None, pizzas=None, extras=None, delivery_persons=None):
        if customers is None:
            customers = self.create_fake_customers(2)
        if pizzas is None:
            pizzas = self.create_fake_pizzas(3)
        if extras is None:
            extras = self.create_fake_extras(4)
        if delivery_persons is None:
            delivery_persons = self.create_fake_delivery_persons(1)
        
        statuses = list(OrderStatus)
        orders = []
        
        for i in range(count):
            customer = random.choice(customers)
            status = random.choice(statuses)
            
            # Create a unique combination of pizzas for this order
            order_pizzas = []
            pizza_count = random.randint(1, min(3, len(pizzas)))
            selected_pizzas = random.sample(pizzas, pizza_count)
            
            for pizza in selected_pizzas:
                quantity = random.randint(1, 3)
                order_pizzas.append({'pizza': pizza, 'quantity': quantity})
            
            order_extras = []
            if extras and random.choice([True, False]):
                order_extras = random.sample(extras, random.randint(1, min(2, len(extras))))
            
            delivery_person = None
            if status != OrderStatus.Pending and delivery_persons:
                delivery_person = random.choice(delivery_persons)
            
            postal_code = customer.postalCode if customer.postalCode else self.faker.postcode()
            
            order = self.order.create(
                user=customer,
                status=status,
                pizzas=order_pizzas,
                extras=order_extras,
                delivery_person=delivery_person,
                postalCode=postal_code
            )
            orders.append(order)
        
        return orders
    
    @db_session
    def create_fake_discount_codes(self, count=1):
        discount_codes = []
        code_prefixes = ['WELCOME', 'SUMMER', 'WINTER', 'SPRING', 'FALL', 'LOYALTY', 'SPECIAL', 'HOLIDAY']
        
        for _ in range(count):
            prefix = random.choice(code_prefixes)
            suffix = random.randint(10, 50)
            code = f"{prefix}{suffix}"
            
            percentage = round(random.uniform(5.0, 30.0), 1)
            valid_until = self.faker.date_time_between(start_date='now', end_date='+1y')
            valid_from = self.faker.date_time_between(start_date='-1y', end_date='now')
            used = random.choice([True, False])
            
            discount_code = self.discount_code.create(
                code=code,
                percentage=percentage,
                valid_until=valid_until,
                valid_from=valid_from,
                used=used
            )
            discount_codes.append(discount_code)
        
        return discount_codes
    
    @db_session
    def create_fake_data(self, ingredients_count=5, extras_count=4, pizzas_count=3,
                        customers_count=2, delivery_persons_count=1, orders_count=2,
                        discount_codes_count=1):
        ingredients = self.create_fake_ingredients(ingredients_count)
        extras = self.create_fake_extras(extras_count)
        pizzas = self.create_fake_pizzas(pizzas_count, ingredients)
        customers = self.create_fake_customers(customers_count)
        delivery_persons = self.create_fake_delivery_persons(delivery_persons_count)
        orders = self.create_fake_orders(orders_count, customers, pizzas, extras, delivery_persons)
        discount_codes = self.create_fake_discount_codes(discount_codes_count)
        
        return {
            'ingredients': ingredients,
            'extras': extras,
            'pizzas': pizzas,
            'customers': customers,
            'delivery_persons': delivery_persons,
            'orders': orders,
            'discount_codes': discount_codes
        }
