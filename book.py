from fastapi import FastAPI, HTTPException, Header
import uvicorn
from pydantic import BaseModel, Field, EmailStr, validator, ConfigDict, field_validator
import re
from datetime import datetime


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
        description="Має містити хоча б одну велику літеру, одну маленьку, одну цифру та один спецсимвол"
    )
    phone_number:str = Field(pattern=r"\+?\d{10,15}")
    model_config = ConfigDict(regex_engine="python-re")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*()_+=\-]", v):
            raise ValueError("Password must contain at least one special character.")
        return v

class Event(BaseModel):
    id: int
    title: str
    description: str
    date: datetime
    location: str





books = {
    1: AddBook(id=1, name="1984", author="George Orwell", year=1949, number=12),
    2: AddBook(id=2, name="To Kill a Mockingbird", author="Harper Lee", year=1960, number=5),
    3: AddBook(id=3, name="The Great Gatsby", author="F. Scott Fitzgerald", year=1925, number=8),
    4: AddBook(id=4, name="Brave New World", author="Aldous Huxley", year=1932, number=10),
    5: AddBook(id=5, name="The Catcher in the Rye", author="J.D. Salinger", year=1951, number=7),
}

users = {
    "user1": RegisterUser(
        name="Andrii",
        surname="Pylypchyk",
        email="andrii@example.com",
        password="StrongPass1!",
        phone_number="+380931234567"
    ),
    "user2": RegisterUser(
        name="Olena",
        surname="Koval",
        email="olena@example.com",
        password="Qwerty12@",
        phone_number="0937654321"
    )
}



events = {
    1: Event(
        id=1,
        title="Python Workshop",
        description="Навчальний воркшоп з Python для початківців",
        date=datetime(2025, 6, 15, 10, 0),
        location="Онлайн"
    ),
    2: Event(
        id=2,
        title="Хакатон зі Штучного Інтелекту",
        description="48-годинний хакатон з розробки AI-рішень",
        date=datetime(2025, 7, 1, 9, 0),
        location="Київ, вул. Хакерська 1"
    )
}



rsvps = {
    1: ["andrii@example.com"],
    2: ["olena@example.com", "test@example.com"]
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
    if id in books:
        return books[id]
    raise HTTPException(status_code=404, detail="Книга не знайдена")



@app.post("/add_user", status_code=201)
async def register_user(register_user: RegisterUser):
    users[f"user{len(users)+1}"] = register_user
    return {"message": "Користувача додано успішно", "user": register_user}




@app.post("/events", status_code=201)
async def create_event(new_event: Event, x_role: str = Header(..., alias="X-Role")):
    if x_role != "admin":
        raise HTTPException(status_code=403, detail="немає прав створювати події")
    if new_event.id in events:
        raise HTTPException(status_code=400, detail="Event exist")
    events[new_event.id] = new_event
    return new_event


@app.get('/events', status_code=200)
async def get_events():
    if events:
        return list(events.values())
    else:
        raise HTTPException(status_code=204, detail="No Content")

@app.get('/events/{id}', status_code=200)
async def get_event(id:int):
    if id in events:
        return events[id]
    else:
        raise HTTPException(status_code=404, detail="Not found")


@app.put("/events/{id}", status_code=200)
async def put_event(id: int, event: Event, x_role: str = Header(..., alias="X-Role")):
    if x_role != "admin":
        raise HTTPException(status_code=403, detail="немає прав змінювати події")
    if id not in events:
        raise HTTPException(status_code=404, detail="Not found")
    if event.id != id:
        raise HTTPException(status_code=400, detail="Bad Request")

    events[id] = event
    return event


@app.delete("/events/{id}", status_code=200)
async def delete_event(id: int, x_role: str = Header(..., alias="X-Role")):
    if x_role != "admin":
        raise HTTPException(status_code=403, detail="немає прав видаляти події")
    if id not in events:
        raise HTTPException(status_code=404, detail="Not found")
    del events[id]
    return {"message": "Подію видалено"}

@app.patch("/events/{id}/reschedule", status_code=200)
async def reschedule_event(id: int, new_date: datetime, x_role: str = Header(..., alias="X-Role")):
    if x_role != "admin":
        raise HTTPException(status_code=403, detail="немає прав переносити події")
    if id not in events:
        raise HTTPException(status_code=404, detail="Not found")
    if new_date < datetime.now():
        raise HTTPException(status_code=400, detail="Bad Request")
    events[id].date = new_date
    return events[id]


@app.post("/events/{id}/rsvp")
async def rsvp_event(id: int, user_email: str):
    if id not in events:
        raise HTTPException(status_code=404, detail="Not found")
    if id not in rsvps:
        rsvps[id] = []
    if user_email in rsvps[id]:
        raise HTTPException(status_code=409, detail="Користувач вже зареєстрований")
    rsvps[id].append(user_email)
    return {"message": "Реєстрація успішна"}


if __name__ == "__main__":
    uvicorn.run("book:app", reload=True)
