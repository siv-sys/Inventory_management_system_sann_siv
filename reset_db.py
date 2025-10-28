import os

def reset_database():
    """Delete old DB and recreate tables."""
    from app import app, db  # import inside function to avoid circular import
   
    db_path = os.path.join(os.path.dirname(__file__), 'inventory_new.db')
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Old database deleted.")
   
    with app.app_context():
        db.create_all()
        print("New database created with updated schema.")
   
    print("Database reset complete!")

if __name__ == '__main__':
    reset_database()