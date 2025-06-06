from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr
import uvicorn
from typing import List
import sqlite3

def init_db():
    connection = sqlite3.connect('products.db')
    cursor = connection.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
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
            FOREIGN KEY(user_id) REFERENCES User(id) ON DELETE CASCADE
        )
    ''')

    connection.commit()
    connection.close()

app = FastAPI(on_startup=[init_db])

class Order(BaseModel):
    product_name: str = Field(...,description="Назва продукту")
    amount: int = Field(1,ge=0, description="Кількість товару")
    price: float = Field(ge=0, description="Ціна товару")

class User(BaseModel):
    name: str = Field(..., description="Ім’я користувача")
    email: EmailStr = Field(..., description="електронна пошта")
    list_of_orders: Order = Field(..., description="Список замовлень користувача")


@app.post("/create_user", status_code=200)
async def create_user(user:User):
    conn = None
    try:
        conn = sqlite3.connect('products.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM User WHERE email = ?', (user.email,))
        existing_user = cursor.fetchone()
        if existing_user:
            conn.close()
            raise HTTPException(status_code=400, detail="Користувач з таким email вже існує")

        cursor.execute(
            'INSERT INTO User (name, email) VALUES (?, ?)',
            (user.name, user.email)
        )
        user_id = cursor.lastrowid

        cursor.execute(
            '''INSERT INTO Orders (user_id, product_name, amount, price) 
               VALUES (?, ?, ?, ?)''',
            (user_id, user.list_of_orders.product_name, user.list_of_orders.amount, user.list_of_orders.price)
        )

        conn.commit()
        conn.close()

        return {"message": f"Користувача '{user.name}' успішно створено з {user.list_of_orders} замовленнями"}
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

        cursor.execute('SELECT id, name, email FROM User WHERE email = ?', (email,))
        user_row = cursor.fetchone()

        if not user_row:
            return {"message": "Користувача з таким email не знайдено"}

        user_id = user_row['id']

        cursor.execute('SELECT product_name, amount, price FROM Orders WHERE user_id = ?', (user_id,))
        order_row = cursor.fetchone()

        if order_row:
            order = {
                "product_name": order_row["product_name"],
                "amount": order_row["amount"],
                "price": order_row["price"]
            }

        return {
            "name": user_row["name"],
            "email": user_row["email"],
            "order": order
        }

    except sqlite3.DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn is not None:
            conn.close()




if __name__ == "__main__":
    uvicorn.run("homework0606:app", reload=True)