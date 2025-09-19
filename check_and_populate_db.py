#!/usr/bin/env python3
"""
Script to check if the database is populated and run create_fake_data.py if needed.
"""

import os
import sys
import subprocess

# Add src to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import init_db
from pony.orm import db_session, select, count
from database.models import Ingredient, Extra, Pizza, Customer, DeliveryPerson, Order, DiscountCode

def is_database_populated():
    """Check if the database has any data in the main tables."""
    with db_session:
        # Check if any of the main tables have data
        ingredient_count = Ingredient.select().count()
        extra_count = Extra.select().count()
        pizza_count = Pizza.select().count()
        customer_count = Customer.select().count()
        delivery_person_count = DeliveryPerson.select().count()
        order_count = Order.select().count()
        discount_code_count = DiscountCode.select().count()
        
        total_count = (ingredient_count + extra_count + pizza_count + 
                      customer_count + delivery_person_count + 
                      order_count + discount_code_count)
        
        print(f"Database record counts:")
        print(f"  Ingredients: {ingredient_count}")
        print(f"  Extras: {extra_count}")
        print(f"  Pizzas: {pizza_count}")
        print(f"  Customers: {customer_count}")
        print(f"  Delivery Persons: {delivery_person_count}")
        print(f"  Orders: {order_count}")
        print(f"  Discount Codes: {discount_code_count}")
        print(f"  Total: {total_count}")
        
        return total_count > 0

def main():
    print("Checking database population...")
    
    # Initialize the database
    print("Initializing database...")
    init_db()
    
    # Check if database is populated
    if is_database_populated():
        print("\nDatabase already contains data. Skipping fake data creation.")
        return
    
    print("\nDatabase is empty. Creating fake data...")
    
    # Run the create_fake_data.py script
    script_path = os.path.join(os.path.dirname(__file__), 'create_fake_data.py')
    try:
        result = subprocess.run([sys.executable, script_path], 
                              check=True, 
                              capture_output=True, 
                              text=True)
        print("Fake data created successfully!")
        print("Output:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error creating fake data: {e}")
        print("Error output:")
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()