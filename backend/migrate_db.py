import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'poetry.db')
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add created_at to reviews
        try:
            cursor.execute("ALTER TABLE reviews ADD COLUMN created_at DATETIME")
            print("Added created_at column to reviews table.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("Column created_at already exists in reviews table.")
            else:
                print(f"Error adding column to reviews: {e}")
                
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error connecting to database: {e}")
