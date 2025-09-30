#!/usr/bin/env python3
"""
Simple script to create fake data with at least 100 orders using Faker.
This script can be run multiple times to add more data without deleting existing records.
"""

import os
import sys
import random
from faker import Faker

# Add src to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import init_db, DataManager
from pony.orm import db_session, select
from database.models import IngredientType, ExtraType, DeliveryStatus, OrderStatus, Ingredient, Extra, Pizza, Customer, Employee, DeliveryPerson, Order

def main():
    # Initialize the database
    print("Initializing database...")
    init_db()
    
    # Create a DataManager instance and Faker instance
    data_manager = DataManager()
    fake = Faker()
    
    # Create all data within a single database session to avoid transaction conflicts
    with db_session:
        # Get existing data using Pony ORM select
        ingredients = list(Ingredient.select())
        extras = list(Extra.select())
        pizzas = list(Pizza.select())
        customers = list(Customer.select())
        delivery_persons = list(DeliveryPerson.select())
        orders = list(Order.select())
        
        existing_ingredients = len(ingredients)
        existing_extras = len(extras)
        existing_pizzas = len(pizzas)
        existing_customers = len(customers)
        existing_delivery_persons = len(delivery_persons)
        existing_orders = len(orders)
        
        print(f"Existing data: {existing_ingredients} ingredients, {existing_extras} extras, {existing_pizzas} pizzas, "
              f"{existing_customers} customers, {existing_delivery_persons} delivery persons, {existing_orders} orders")
        
        # Only create basic data if we don't have enough
        if existing_ingredients < 5:
            print("Creating additional ingredients...")
            ingredient_names = [
                'Tomato Sauce', 'Mozzarella', 'Pepperoni', 'Mushrooms', 'Basil',
                'Olives', 'Ham', 'Pineapple', 'Onions', 'Bell Peppers',
                'Chicken', 'Bacon', 'Tomatoes', 'Oregano', 'Garlic'
            ]
            
            ingredients_data = []
            for _ in range(10 - existing_ingredients):
                name = random.choice(ingredient_names)
                price = round(random.uniform(0.3, 2.0), 2)
                ingredient_type = random.choice(list(IngredientType))
                ingredients_data.append({'name': name, 'price': price, 'type': ingredient_type})
            
            new_ingredients = data_manager.ingredient.create_batch(ingredients_data)
            ingredients.extend(new_ingredients)
            print(f"Added {len(new_ingredients)} new ingredients")
        else:
            print(f"Using existing {len(ingredients)} ingredients")
        
        if existing_extras < 4:
            print("Creating additional extras...")
            drink_names = ['Coca Cola', 'Sprite', 'Fanta', 'Water', 'Orange Juice', 'Iced Tea']
            dessert_names = ['Ice Cream', 'Tiramisu', 'Cheesecake', 'Chocolate Cake', 'Apple Pie']
            
            extras_data = []
            for _ in range(6 - existing_extras):
                if random.choice([True, False]):
                    name = random.choice(drink_names)
                    extra_type = ExtraType.Drink
                else:
                    name = random.choice(dessert_names)
                    extra_type = ExtraType.Dessert
                
                price = round(random.uniform(1.5, 5.0), 2)
                extras_data.append({'name': name, 'price': price, 'type': extra_type})
            
            new_extras = data_manager.extra.create_batch(extras_data)
            extras.extend(new_extras)
            print(f"Added {len(new_extras)} new extras")
        else:
            print(f"Using existing {len(extras)} extras")
        
        if existing_pizzas < 3:
            print("Creating additional pizzas...")
            pizza_names = ['Margherita', 'Pepperoni', 'Hawaiian', 'Vegan Special', 'Veggie Delight']
            
            for _ in range(5 - existing_pizzas):
                name = random.choice(pizza_names)
                description = f"Delicious {name.lower()} pizza with fresh ingredients"
                
                pizza_ingredients = random.sample(ingredients, random.randint(2, min(5, len(ingredients))))
                
                pizza = data_manager.pizza.create(name=name, description=description, ingredients=pizza_ingredients)
                pizzas.append(pizza)
            print(f"Added {5 - existing_pizzas} new pizzas")
        else:
            print(f"Using existing {len(pizzas)} pizzas")
        
        if existing_delivery_persons < 2:
            print("Creating additional delivery persons...")
            positions = ['Delivery Driver', 'Senior Delivery Driver', 'Delivery Manager']
            statuses = list(DeliveryStatus)
            
            for _ in range(3 - existing_delivery_persons):
                first_name = fake.first_name()
                last_name = fake.last_name()
                username = f"delivery_{first_name.lower()}{random.randint(1, 999)}"
                email = f"{username}@{fake.free_email_domain()}"
                
                position = random.choice(positions)
                salary = round(random.uniform(1800.0, 2500.0), 2)
                status = random.choice(statuses)
                phone = fake.phone_number()
                gender = random.choice(['Male', 'Female', 'Other'])
                
                password = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
                delivery_person = data_manager.delivery_person.create(
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
            print(f"Added {3 - existing_delivery_persons} new delivery persons")
        else:
            print(f"Using existing {len(delivery_persons)} delivery persons")
        
        # Always create more customers (focus on adding users)
        print("Creating additional customers...")
        new_customers = []
        
        for _ in range(10):  # Always add 10 new customers
            first_name = fake.first_name()
            last_name = fake.last_name()
            username = f"{first_name.lower()}_{last_name.lower()}{random.randint(1, 999)}"
            email = f"{username}@{fake.free_email_domain()}"
            
            birthdate = fake.date_of_birth(minimum_age=18, maximum_age=70)
            address = fake.street_address()
            postal_code = fake.postcode()
            phone = fake.phone_number()
            gender = random.choice(['Male', 'Female', 'Other'])
            loyalty_points = random.randint(0, 500)
            birthday_order = random.choice([True, False])
            
            password = fake.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
            customer = data_manager.customer.create(
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
            new_customers.append(customer)
        
        customers.extend(new_customers)
        print(f"Added {len(new_customers)} new customers (total: {len(customers)})")
        
        # Always create more orders (main focus)
        print("Creating 100 additional orders...")
        statuses = list(OrderStatus)
        orders = []
        
        for i in range(100):
            customer = random.choice(customers)
            status = random.choice(statuses)
            
            # Create unique pizza combinations by using different quantities
            order_pizzas = []
            pizza_count = random.randint(1, min(3, len(pizzas)))
            selected_pizzas = random.sample(pizzas, pizza_count)
            
            for pizza in selected_pizzas:
                # Use a unique quantity for each pizza to avoid duplicate relations
                quantity = (i % 3) + 1  # This will vary between 1-3 based on the order index
                order_pizzas.append({'pizza': pizza, 'quantity': quantity})
            
            order_extras = []
            if extras and random.choice([True, False]):
                order_extras = random.sample(extras, random.randint(1, min(2, len(extras))))
            
            delivery_person = None
            if status != OrderStatus.Pending and delivery_persons:
                delivery_person = random.choice(delivery_persons)
            
            postal_code = customer.postalCode if customer.postalCode else fake.postcode()
            
            order = data_manager.order.create(
                user=customer,
                status=status,
                pizzas=order_pizzas,
                extras=order_extras,
                delivery_person=delivery_person,
                postalCode=postal_code
            )
            orders.append(order)
    
    print(f"Total ingredients: {len(ingredients)}")
    print(f"Total extras: {len(extras)}")
    print(f"Total pizzas: {len(pizzas)}")
    print(f"Total customers: {len(customers)}")
    print(f"Total delivery persons: {len(delivery_persons)}")
    print(f"Total orders: {len(orders)}")
    
    print("\nFake data creation completed successfully!")
    print("You can run this script multiple times to add more data.")

if __name__ == "__main__":
    main()