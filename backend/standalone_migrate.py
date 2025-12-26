import pymysql
from config import Config

def migrate():
    # 解析连接字符串 (mysql+pymysql://root:123456@localhost/poetry_db)
    # 这里直接连接
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        database='poetry_db',
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # 1. 检查字段是否存在
            cursor.execute("SHOW COLUMNS FROM users LIKE 'password_hash'")
            result = cursor.fetchone()
            
            if not result:
                print("正在添加 password_hash 字段...")
                cursor.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(128) DEFAULT '123456'")
            else:
                print("字段 password_hash 已存在。")
            
            # 2. 更新所有用户密码为 123456
            print("正在同步初始密码...")
            cursor.execute("UPDATE users SET password_hash = '123456'")
            
        connection.commit()
        print("数据库迁移完成！")
    except Exception as e:
        print(f"迁移出错: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    migrate()
