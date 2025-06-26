from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr
import uvicorn
from typing import List
import sqlite3

def init_db():
    connection = sqlite3.connect('products.db')
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            amount INTEGER NOT NULL CHECK(amount > 0),
            price FLOAT NOT NULL CHECK(price >= 0),
            FOREIGN KEY(user_id) REFERENCES Users(id) ON DELETE CASCADE
        )
    ''')

    connection.commit()
    connection.close()

app = FastAPI(on_startup=[init_db])

class Order(BaseModel):
    product_name: str = Field(..., description="Назва продукту")
    amount: int = Field(1, gt=0, description="Кількість товару")
    price: float = Field(gt=0, description="Ціна товару")

class User(BaseModel):
    name: str = Field(..., description="Ім’я користувача")
    email: EmailStr = Field(..., description="електронна пошта")
    orders: list[Order] = Field(default_factory=list, description="Список замовлень користувача")


@app.post("/create_user", status_code=200)
async def create_user(user: User):
    conn = None
    try:
        conn = sqlite3.connect('products.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM Users WHERE email = ?', (user.email,))
        existing_user = cursor.fetchone()
        if existing_user:
            raise HTTPException(status_code=400, detail="Користувач з таким email вже існує")

        cursor.execute(
            'INSERT INTO Users (name, email) VALUES (?, ?)',
            (user.name, user.email)
        )
        user_id = cursor.lastrowid

        orders = [
            Order(product_name=data.product_name, amount=data.amount, price=data.price).model_dump()
            for data in user.orders
        ]

        query_data = []
        for order in orders:
            order["user_id"] = user_id
            query_data.append(tuple(order.values()))

        if query_data:
            cursor.executemany(
                """INSERT INTO Orders (product_name, amount, price, user_id) 
                   VALUES (?, ?, ?, ?)""",
                query_data,
            )

        conn.commit()

        return {"message": f"Користувача '{user.name}' успішно створено з {len(user.orders)} замовленнями"}
    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn is not None:
            conn.close()


@app.get("/get_user")
async def get_user(email: str):
    conn = None
    try:
        conn = sqlite3.connect('products.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT id, name, email FROM Users WHERE email = ?', (email,))
        user_row = cursor.fetchone()

        if not user_row:
            raise HTTPException(status_code=404, detail="Користувача з таким email не знайдено")

        user_id = user_row['id']

        cursor.execute('SELECT product_name, amount, price FROM Orders WHERE user_id = ?', (user_id,))
        order_rows = cursor.fetchall()

        orders = [
            {
                "product_name": row["product_name"],
                "amount": row["amount"],
                "price": row["price"]
            }
            for row in order_rows
        ]

        return {
            "name": user_row["name"],
            "email": user_row["email"],
            "orders": orders,
        }

    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    uvicorn.run("homework0606:app", reload=True)
