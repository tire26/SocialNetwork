import psycopg2
import os
from passlib.context import CryptContext

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/users_db")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL
    );
    """)

    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
    """)

    cursor.execute("SELECT COUNT(*) FROM users;")
    count = cursor.fetchone()[0]

    if count == 0:
        hashed_admin = get_password_hash("adminpass")
        hashed_testuser = get_password_hash("testpass")

        cursor.execute("""
        INSERT INTO users (username, password)
        VALUES 
            ('admin', %s),
            ('testuser', %s);
        """, (hashed_admin, hashed_testuser))

        print("Тестовые пользователи добавлены.")

    conn.commit()
    cursor.close()
    conn.close()
    print("Инициализация базы данных завершена.")


if __name__ == "__main__":
    init_db()