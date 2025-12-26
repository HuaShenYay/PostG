from backend.app import app, db
from sqlalchemy import text

def add_password_column():
    with app.app_context():
        try:
            # 尝试添加列
            db.session.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(128) DEFAULT '123456'"))
            db.session.commit()
            print("成功为 user 表添加了 password_hash 字段。")
        except Exception as e:
            # 如果列已经存在，会报错，这里可以捕获
            print(f"操作提示（可能字段已存在）: {e}")
            db.session.rollback()
            
        # 确保所有现有用户的密码都被设置为 123456
        try:
            db.session.execute(text("UPDATE users SET password_hash = '123456' WHERE password_hash IS NULL OR password_hash = ''"))
            db.session.commit()
            print("已将所有现有用户的初始密码设置为 123456。")
        except Exception as e:
            print(f"更新密码时出错: {e}")

if __name__ == "__main__":
    add_password_column()
