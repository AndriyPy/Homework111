from fastapi import FastAPI, HTTPException, status
import uvicorn
from pydanticurok import BaseModel, Field, EmailStr, validator
import re

app = FastAPI()

class AddBook(BaseModel):
    id: int
    name: str = Field(..., description="Назва книги")
    author: str = Field(..., description="Автор книги")
    year: int
    number: int

class RegisterUser(BaseModel):
    name: str = Field(min_length=2)
    surname: str = Field(min_length=2)
    email: EmailStr = Field(description="email")
    password: str = Field(
        min_length=8,
        pattern=r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).+$',
        description="Має містити хоча б одну велику літеру, одну маленьку, одну цифру та один спецсимвол"
    )
    phone_number:str = Field(pattern=r"\+?\d{10,15}")


books= {
    "book1": AddBook(
        id=1,
        name="1984",
        author="George Orwell",
        year=1949,
        number=12
    ),
    "book2": AddBook(
        id=2,
        name="To Kill a Mockingbird",
        author="Harper Lee",
        year=1960,
        number=5
    ),
    "book3": AddBook(
        id=3,
        name="The Great Gatsby",
        author="F. Scott Fitzgerald",
        year=1925,
        number=8
    ),
    "book4": AddBook(
        id=4,
        name="Brave New World",
        author="Aldous Huxley",
        year=1932,
        number=10
    ),
    "book5": AddBook(
        id=5,
        name="The Catcher in the Rye",
        author="J.D. Salinger",
        year=1951,
        number=7
    ),
}

users = {
    "user1": RegisterUser(
        name="Andrii",
        surname="Pylypchyk",
        email="andrii@example.com",
        password="StrongPass1!",
        phone="+380931234567"
    ),
    "user2": RegisterUser(
        name="Olena",
        surname="Koval",
        email="olena@example.com",
        password="Qwerty12@",
        phone="0937654321"
    )
}


@app.get("/books", status_code=200)
async def get_books():
    return list(books.values())

@app.post("/add_book/", status_code=201)
async def add_book(add_book: AddBook):
    if add_book.id in books:
        raise HTTPException(status_code=400, detail="Книга з таким ID вже існує")

    books[add_book.id] = add_book
    return list(books.values())

@app.get("/books/{id}", status_code=200)
async def get_one_book(id: int):
    for book in books.values():
        if book.id == id:
            return book
    raise HTTPException(status_code=404, detail="Книга не знайдена")



@app.post("/add_user", status_code=201)
async def register_user(register_user: RegisterUser):
    users[f"user{len(users)+1}"] = register_user
    return {"message": "Користувача додано успішно", "user": register_user}





if __name__ == "__main__":
    uvicorn.run("book:app", reload=True)
