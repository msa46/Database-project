#!/usr/bin/env python3
"""
Example script to demonstrate how to use the DataManager to create fake data using Faker.
"""

import os
import sys

# Add src to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import init_db, DataManager
from pony.orm import db_session

def main():
    # Initialize the database
    print("Initializing database...")
    init_db()
    
    # Create a DataManager instance
    data_manager = DataManager()
    
    # Use a single database session for all operations
    @db_session
    def create_data():
        # Create fake data using the Faker-based method
        fake_data = data_manager.create_fake_data(
            ingredients_count=8,
            extras_count=6,
            pizzas_count=5,
            customers_count=4,
            delivery_persons_count=2,
            orders_count=5,
            discount_codes_count=3
        )
        
        print("Initial fake data created successfully!")
        
        # Create more ingredients
        more_ingredients = data_manager.ingredient.create_batch([
            {'name': data_manager.faker.word(), 'price': round(data_manager.faker.random.uniform(0.3, 2.0), 2), 'type': data_manager.faker.random_element(list(data_manager.ingredient.type.py_type))}
            for _ in range(3)
        ])
        print("Created more ingredients!")
        
        # Create more extras
        more_extras = data_manager.extra.create_batch([
            {'name': data_manager.faker.word(), 'price': round(data_manager.faker.random.uniform(1.5, 5.0), 2), 'type': data_manager.faker.random_element(list(data_manager.extra.type.py_type))}
            for _ in range(2)
        ])
        print("Created more extras!")
        
        # Create more pizzas using all ingredients
        all_ingredients = fake_data['ingredients'] + more_ingredients
        more_pizzas = []
        for _ in range(2):
            name = data_manager.faker.word().title()
            description = f"{data_manager.faker.sentence(nb_words=6)} Perfect with {data_manager.faker.random_element(['extra cheese', 'fresh herbs', 'spicy sauce', 'crispy crust', 'premium toppings'])}."
            pizza_ingredients = data_manager.faker.random_sample(all_ingredients, length=data_manager.faker.random_int(min=2, max=min(5, len(all_ingredients))))
            # Add random stock between 2 and 100 for each pizza
            stock = data_manager.faker.random_int(min=2, max=100)
            pizza = data_manager.pizza.create(name=name, description=description, ingredients=pizza_ingredients, stock=stock)
            more_pizzas.append(pizza)
        print("Created more pizzas!")
        
        # Create more customers
        more_customers = []
        for _ in range(2):
            first_name = data_manager.faker.first_name()
            last_name = data_manager.faker.last_name()
            username = f"{first_name.lower()}_{last_name.lower()}"
            email = f"{username}@{data_manager.faker.free_email_domain()}"
            password = data_manager.faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
            birthdate = data_manager.faker.date_of_birth(minimum_age=18, maximum_age=70)
            address = data_manager.faker.street_address()
            postal_code = data_manager.faker.postcode()
            phone = data_manager.faker.phone_number()
            gender = data_manager.faker.random_element([data_manager.faker.random_element(['M', 'F']), 'Other']) if data_manager.faker.boolean() else 'Other'
            loyalty_points = data_manager.faker.random_int(min=0, max=500)
            birthday_order = data_manager.faker.boolean()
            
            customer = data_manager.customer.create_full_user(
                username=username,
                email=email,
                password=password,
                address=address,
                postalCode=postal_code,
                phone=phone,
                Gender=gender,
                birthdate=birthdate,
                loyalty_points=loyalty_points,
                birthday_order=birthday_order
            )
            more_customers.append(customer)
        print("Created more customers!")
        
        # Create more delivery persons
        more_delivery_persons = []
        positions = [data_manager.faker.job() for _ in range(3)]
        statuses = list(data_manager.delivery_person.status.py_type)
        
        for _ in range(1):
            first_name = data_manager.faker.first_name()
            last_name = data_manager.faker.last_name()
            username = f"delivery_{first_name.lower()}"
            email = f"{username}@{data_manager.faker.free_email_domain()}"
            password = data_manager.faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
            position = data_manager.faker.random_element(positions)
            salary = round(data_manager.faker.random.uniform(1800.0, 2500.0), 2)
            status = data_manager.faker.random_element(statuses)
            phone = data_manager.faker.phone_number()
            gender = data_manager.faker.random_element([data_manager.faker.random_element(['M', 'F']), 'Other']) if data_manager.faker.boolean() else 'Other'
            
            delivery_person = data_manager.delivery_person.create_full_user(
                username=username,
                email=email,
                password=password,
                address=data_manager.faker.street_address(),
                postalCode=data_manager.faker.postcode(),
                phone=phone,
                Gender=gender,
                position=position,
                salary=salary,
                status=status
            )
            more_delivery_persons.append(delivery_person)
        print("Created more delivery persons!")
        
        # Create more orders using existing entities
        all_customers = fake_data['customers'] + more_customers
        all_pizzas = fake_data['pizzas'] + more_pizzas
        all_extras = fake_data['extras'] + more_extras
        all_delivery_persons = fake_data['delivery_persons'] + more_delivery_persons
        
        more_orders = []
        statuses = list(data_manager.order.status.py_type)
        
        for _ in range(3):
            customer = data_manager.faker.random_element(all_customers)
            status = data_manager.faker.random_element(statuses)
            
            # Create a unique combination of pizzas for this order
            order_pizzas = []
            pizza_count = data_manager.faker.random_int(min=1, max=min(3, len(all_pizzas)))
            selected_pizzas = data_manager.faker.random_sample(all_pizzas, length=pizza_count)
            
            for pizza in selected_pizzas:
                quantity = data_manager.faker.random_int(min=1, max=3)
                order_pizzas.append({'pizza': pizza, 'quantity': quantity})
            
            order_extras = []
            if all_extras and data_manager.faker.boolean():
                extras_count = data_manager.faker.random_int(min=1, max=min(2, len(all_extras)))
                order_extras = data_manager.faker.random_sample(all_extras, length=extras_count)
            
            delivery_person = None
            if status != data_manager.order.status.py_type.Pending and all_delivery_persons:
                delivery_person = data_manager.faker.random_element(all_delivery_persons)
            
            postal_code = customer.postalCode if customer.postalCode else data_manager.faker.postcode()
            
            order = data_manager.order.create(
                user=customer,
                status=status,
                pizzas=order_pizzas,
                extras=order_extras,
                delivery_person=delivery_person,
                postalCode=postal_code
            )
            more_orders.append(order)
        print("Created more orders!")
        
        # Create more discount codes
        more_discount_codes = []
        code_prefixes = [data_manager.faker.word().upper() for _ in range(5)]
        
        for _ in range(2):
            prefix = data_manager.faker.random_element(code_prefixes)
            suffix = data_manager.faker.random_int(min=10, max=99)
            code = f"{prefix}{suffix}"
            
            percentage = round(data_manager.faker.random.uniform(5.0, 30.0), 1)
            valid_until = data_manager.faker.date_time_between(start_date='now', end_date='+1y')
            valid_from = data_manager.faker.date_time_between(start_date='-1y', end_date='now')
            used = data_manager.faker.boolean()
            
            discount_code = data_manager.discount_code.create(
                code=code,
                percentage=percentage,
                valid_until=valid_until,
                valid_from=valid_from,
                used=used
            )
            more_discount_codes.append(discount_code)
        print("Created more discount codes!")
        
        # Create a specific ingredient
        from database.models import IngredientType
        data_manager.ingredient.create(name='Cheese', price=1.0, type=IngredientType.Vegetarian)
        print("Created Cheese ingredient!")
        
        print("All fake data created successfully!")

if __name__ == "__main__":
    main()