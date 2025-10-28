import os
import sqlite3
from glob import glob

def clean_database():
    # Remove all database files
    db_files = glob('*.db') + glob('*.db-journal')
    for db_file in db_files:
        try:
            os.remove(db_file)
            print(f"Removed: {db_file}")
        except Exception as e:
            print(f"Could not remove {db_file}: {e}")
    
    # Also check for any .sqlite files
    sqlite_files = glob('*.sqlite')
    for sqlite_file in sqlite_files:
        try:
            os.remove(sqlite_file)
            print(f"Removed: {sqlite_file}")
        except Exception as e:
            print(f"Could not remove {sqlite_file}: {e}")

def verify_database_clean():
    db_files = glob('*.db') + glob('*.db-journal') + glob('*.sqlite')
    if db_files:
        print("WARNING: Database files still exist:")
        for file in db_files:
            print(f"  - {file}")
        return False
    else:
        print("✓ Database cleaned successfully")
        return True

if __name__ == '__main__':
    print("Cleaning database files...")
    clean_database()
    verify_database_clean()
    print("\nNow run: python app.py")