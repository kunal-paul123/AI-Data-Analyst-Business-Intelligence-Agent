# seed_data.py — Generates and loads realistic fake e-commerce data into the database
# Run this once with: uv run python data/seed_data.py

import sys
import os
import random
import asyncio                          # Required to run async functions from a script
from datetime import date, timedelta

from faker import Faker
from sqlalchemy import select, func     # 'select' replaces db.query() in async SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, AsyncSessionLocal
from backend.models import Base, Customer, Product, Order, OrderItem

# Initialize Faker with Indian locale for realistic names and cities
fake = Faker("en_IN")

# Seed random so results are reproducible (same data every run)
random.seed(42)
fake.seed_instance(42)

# ─────────────────────────────────────────────
# CONFIGURATION — tweak these to change data volume
# ─────────────────────────────────────────────
NUM_CUSTOMERS = 500
NUM_PRODUCTS = 50
NUM_ORDERS = 2000
DAYS_OF_HISTORY = 365   # Generate 12 months of past orders


# ─────────────────────────────────────────────
# PRODUCT CATALOG — fixed categories and products
# ─────────────────────────────────────────────

# Each tuple: (product name, category, min price, max price)
PRODUCT_CATALOG = [
    # Electronics (high value)
    ("Wireless Earbuds", "Electronics", 1500, 4000),
    ("Bluetooth Speaker", "Electronics", 2000, 6000),
    ("USB-C Hub", "Electronics", 800, 2500),
    ("Mechanical Keyboard", "Electronics", 3000, 8000),
    ("Gaming Mouse", "Electronics", 1200, 4000),
    ("Webcam HD", "Electronics", 1500, 4500),
    ("Smart Watch", "Electronics", 5000, 15000),
    ("Power Bank 20000mAh", "Electronics", 1200, 3000),
    ("LED Desk Lamp", "Electronics", 600, 2000),
    ("Portable SSD 1TB", "Electronics", 4000, 9000),

    # Clothing
    ("Men's Casual Shirt", "Clothing", 400, 1200),
    ("Women's Kurti", "Clothing", 350, 1000),
    ("Denim Jeans", "Clothing", 800, 2500),
    ("Sports T-Shirt", "Clothing", 300, 900),
    ("Winter Jacket", "Clothing", 1500, 5000),
    ("Running Shoes", "Clothing", 1200, 4000),
    ("Cotton Socks (Pack of 5)", "Clothing", 150, 400),
    ("Formal Trousers", "Clothing", 700, 2000),
    ("Saree", "Clothing", 500, 3000),
    ("Hoodie", "Clothing", 600, 2000),

    # Books
    ("Python Crash Course", "Books", 350, 600),
    ("Atomic Habits", "Books", 250, 450),
    ("The Alchemist", "Books", 150, 300),
    ("System Design Interview", "Books", 500, 900),
    ("Clean Code", "Books", 400, 700),
    ("Data Structures in Python", "Books", 350, 650),
    ("The Psychology of Money", "Books", 200, 400),
    ("Deep Work", "Books", 250, 450),
    ("NCERT Class 12 Physics", "Books", 100, 200),
    ("Ikigai", "Books", 180, 350),

    # Home & Kitchen
    ("Stainless Steel Water Bottle", "Home & Kitchen", 300, 800),
    ("Non-Stick Frying Pan", "Home & Kitchen", 500, 1500),
    ("Air Fryer 4L", "Home & Kitchen", 3000, 7000),
    ("Coffee Maker", "Home & Kitchen", 1500, 5000),
    ("Electric Kettle", "Home & Kitchen", 600, 2000),
    ("Dinner Set (12 pcs)", "Home & Kitchen", 800, 2500),
    ("Mixer Grinder", "Home & Kitchen", 2000, 5000),
    ("Chopping Board Set", "Home & Kitchen", 300, 900),
    ("Storage Containers Set", "Home & Kitchen", 400, 1200),
    ("Microwave Oven 20L", "Home & Kitchen", 5000, 12000),

    # Sports & Fitness
    ("Yoga Mat", "Sports", 400, 1200),
    ("Resistance Bands Set", "Sports", 300, 800),
    ("Dumbbells 5kg Pair", "Sports", 700, 2000),
    ("Jump Rope", "Sports", 150, 500),
    ("Cycling Helmet", "Sports", 800, 2500),
    ("Badminton Racket Set", "Sports", 500, 2000),
    ("Cricket Bat", "Sports", 600, 3000),
    ("Gym Gloves", "Sports", 300, 800),
    ("Foam Roller", "Sports", 500, 1500),
    ("Sports Water Bottle", "Sports", 250, 700),
]


# ─────────────────────────────────────────────
# HELPER — revenue multiplier for simulating dips
# ─────────────────────────────────────────────

def get_revenue_multiplier(order_date: date) -> float:
    """
    Returns a multiplier to simulate revenue decline in certain months.
    This makes the data interesting for the 'why did revenue decline?' question.
    The last 2 months will have 25-50% lower revenue than other months.
    This function is plain (not async) since it's just math — no DB involved.
    """
    today = date.today()
    if order_date.year == today.year and order_date.month in [today.month - 1, today.month - 2]:
        return random.uniform(0.5, 0.75)   # Simulate a 25-50% revenue dip
    return 1.0


# ─────────────────────────────────────────────
# ASYNC DB FUNCTIONS
# ─────────────────────────────────────────────

async def create_products(db: AsyncSession) -> list[Product]:
    """Create all products from the catalog and save to DB."""
    products = []
    for name, category, min_price, max_price in PRODUCT_CATALOG:
        product = Product(
            name=name,
            category=category,
            # Round price to nearest 10 for realistic INR values
            price=round(random.uniform(min_price, max_price) / 10) * 10,
            stock=random.randint(50, 500),
        )
        db.add(product)        # db.add() is synchronous — just registers the object
        products.append(product)

    await db.commit()          # 'await' because writing to DB is an async I/O operation
    print(f"Created {len(products)} products")
    return products


async def create_customers(db: AsyncSession) -> list[Customer]:
    """Create fake customers using Faker and save to DB."""
    customers = []
    emails_seen = set()   # Track used emails to avoid unique constraint violations

    for _ in range(NUM_CUSTOMERS):
        email = fake.email()
        # Regenerate if email already used (Faker can produce duplicates)
        while email in emails_seen:
            email = fake.email()
        emails_seen.add(email)

        # signup_date is sometime in the last 2 years
        signup_date = date.today() - timedelta(days=random.randint(1, 730))

        customer = Customer(
            name=fake.name(),
            email=email,
            city=fake.city(),
            signup_date=signup_date,
        )
        db.add(customer)
        customers.append(customer)

    await db.commit()   # Persist all 500 customers to DB in one transaction
    print(f"Created {len(customers)} customers")
    return customers


async def create_orders(
    db: AsyncSession,
    customers: list[Customer],
    products: list[Product]
) -> None:
    """
    Create realistic orders spread across the last 12 months.
    Each order has 1-5 line items (OrderItems).
    """
    orders_created = 0

    for _ in range(NUM_ORDERS):
        # Pick a random customer
        customer = random.choice(customers)

        # Pick a random date within the last DAYS_OF_HISTORY days
        order_date = date.today() - timedelta(days=random.randint(0, DAYS_OF_HISTORY))

        # Most orders are completed; some are cancelled or returned
        status = random.choices(
            ["completed", "cancelled", "returned"],
            weights=[85, 10, 5]   # 85% completed, 10% cancelled, 5% returned
        )[0]

        # Pick 1-5 random unique products for this order
        num_items = random.randint(1, 5)
        selected_products = random.sample(products, min(num_items, len(products)))

        # Get the revenue multiplier for this date (simulates monthly revenue dips)
        multiplier = get_revenue_multiplier(order_date)

        order_total = 0.0
        order_items = []

        for product in selected_products:
            quantity = random.randint(1, 3)

            # Slightly vary the price (±10%) to simulate discounts/surge pricing
            unit_price = round(product.price * random.uniform(0.9, 1.1) * multiplier, 2)
            subtotal = round(unit_price * quantity, 2)
            order_total += subtotal

            order_items.append(OrderItem(
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
            ))

        # Skip orders with zero or negative total (edge case safety check)
        if order_total <= 0:
            continue

        order = Order(
            customer_id=customer.id,
            order_date=order_date,
            status=status,
            total_amount=round(order_total, 2),
        )
        db.add(order)

        # flush() sends the INSERT to DB and assigns order.id — without committing yet
        # This is needed so we can link OrderItems to the new order.id
        await db.flush()

        # Now we have order.id — link each item to this order
        for item in order_items:
            item.order_id = order.id
            db.add(item)

        orders_created += 1

    await db.commit()   # Commit all orders and their items in one final transaction
    print(f"Created {orders_created} orders with line items")


async def get_count(db: AsyncSession, model) -> int:
    """
    Helper to count rows in a table using async SQLAlchemy.
    In async mode, db.query() doesn't exist — we use db.execute(select(...)) instead.
    """
    result = await db.execute(select(func.count()).select_from(model))
    return result.scalar()   # .scalar() returns the single integer count value


# ─────────────────────────────────────────────
# MAIN — entry point
# ─────────────────────────────────────────────

async def main():
    print("Starting database seed...\n")

    # Create all tables defined in models.py
    # In async mode, we can't call engine.create_all() directly
    # We use engine.begin() to get an async connection, then run the sync create_all inside it
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created\n")

    # Open a single async session for all inserts using 'async with'
    # The session is automatically closed when the 'async with' block exits
    async with AsyncSessionLocal() as db:
        try:
            # Check if data already exists to avoid duplicates on re-run
            count = await get_count(db, Customer)
            if count > 0:
                print("Database already has data. Delete ecommerce.db and re-run to reseed.")
                return

            products = await create_products(db)
            customers = await create_customers(db)
            await create_orders(db, customers, products)

            # Print final summary counts
            print("\nSeed complete! Database is ready.")
            print(f"Products : {await get_count(db, Product)}")
            print(f"Customers: {await get_count(db, Customer)}")
            print(f"Orders   : {await get_count(db, Order)}")
            print(f"Items    : {await get_count(db, OrderItem)}")

        except Exception as e:
            # Roll back any partial inserts if something goes wrong mid-way
            await db.rollback()
            print(f"Error during seeding: {e}")
            raise


# asyncio.run() is the standard way to launch an async function from a plain script
# It creates an event loop, runs main(), then closes the loop when done
if __name__ == "__main__":
    asyncio.run(main())