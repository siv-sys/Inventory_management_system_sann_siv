import os
from app import app, db

# Remove existing database
if os.path.exists('inventory.db'):
    os.remove('inventory.db')
    print("Removed old database")

# Create new database with tables
with app.app_context():
    db.create_all()
    print("Created new database with all tables")
    print("Database schema should now include user.name column")