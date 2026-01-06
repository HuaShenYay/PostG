from app import app
from models import db
from sqlalchemy import text

def migrate():
    with app.app_context():
        print("开始同步数据库结构...")
        try:
            # 尝试添加列 (MySQL 语法)
            # 注意：如果列已存在，这会报错，我们在 try 块里捕获它
            with db.engine.connect() as conn:
                try:
                    conn.execute(text("ALTER TABLE reviews ADD COLUMN topic_distribution TEXT"))
                    print("已添加 Review.topic_distribution 列")
                except Exception as e:
                    print(f"Review.topic_distribution 可能已存在: {e}")
                
                try:
                    conn.execute(text("ALTER TABLE users ADD COLUMN preference_topics TEXT"))
                    print("已添加 User.preference_topics 列")
                except Exception as e:
                    print(f"User.preference_topics 可能已存在: {e}")
                
                conn.commit()
            print("数据库结构同步完成。")
        except Exception as e:
            print(f"同步过程中出现错误: {e}")

if __name__ == "__main__":
    migrate()
