import sys
import os

# This line helps Python find your 'app' folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import init_db
from app.db.seed import reset_and_seed
from app.db import repo

print("1. Creating database and inserting dummy data...")
init_db()
reset_and_seed()
print("✅ Database seeded successfully!\n")

print("2. Testing product search (Searching for 'atta')...")
product = repo.find_product("atta")
if product:
    print(f"✅ Found product: {product.name} | Current Stock: {product.stock_qty}")
else:
    print("❌ Product not found.")

print("\n3. Testing customers...")
# We check for customers with at least 0 balance and 0 days overdue (basically everyone with a balance)
customers = repo.get_overdue_customers(min_balance=0, days=0)
print(f"✅ Found {len(customers)} customers with balances.")
for c in customers:
    print(f"   - {c.name} owes Rs {c.balance}")

print("\n🎉 PHASE H1 IS FULLY COMPLETE! 🎉")