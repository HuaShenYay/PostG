from app import app, db
from sqlalchemy import text

def run_migration():
    with app.app_context():
        with db.engine.connect() as conn:
            cols = [
                ("dynasty", "VARCHAR(20) DEFAULT 'Tang'"),
                ("translation", "TEXT"),
                ("appreciation", "TEXT"),
                ("author_bio", "TEXT"),
                ("notes", "TEXT")
            ]
            
            for col_name, col_type in cols:
                try:
                    # MySQL syntax
                    sql = text(f"ALTER TABLE poems ADD COLUMN {col_name} {col_type};")
                    conn.execute(sql)
                    print(f"Added column: {col_name}")
                except Exception as e:
                    # 1060: Duplicate column name
                    if "Duplicate column name" in str(e):
                        print(f"Column already exists: {col_name}")
                    else:
                        print(f"Error adding {col_name}: {e}")

if __name__ == "__main__":
    run_migration()
