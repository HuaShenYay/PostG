from app import app
from models import db
from sqlalchemy import text

def migrate():
    with app.app_context():
        print(">>> Attempting to add created_at column to reviews table...")
        try:
            # Check if column exists (MySQL specific query or try-catch)
            try:
                db.session.execute(text("ALTER TABLE reviews ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
                db.session.commit()
                print("Column created_at added successfully.")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("Column created_at already exists.")
                else:
                    raise e
        except Exception as e:
            print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate()
