from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Path,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
import uuid
import aiosqlite
import base64
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import BaseModel, EmailStr, SecretStr, Field
import uvicorn
from fastapi.security import (
    HTTPBasic,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    HTTPBasicCredentials
)
from websockethwdb import hash_password, check_password, create_tables, get_db


BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security = HTTPBasic()

app = FastAPI(on_startup=(create_tables,))


class User(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=4, max_length=64)


class Token(BaseModel):
    token_type: str = Field(description="type of the token", examples=["bearer"])
    access_token: str = Field(description="token value", examples=["#3HM4J24V324kljn2"])


class ConnectionManager:
    def __init__(self):
        self.active_connection: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connection.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connection.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connection:
            await connection.send_text(message)

manager = ConnectionManager()


async def get_user(
    token: str = Depends(oauth2_scheme),
    connection: aiosqlite.Connection = Depends(get_db)
):
    async with connection.cursor() as cursor:
        await cursor.execute(
            "SELECT * FROM users WHERE email = ?", (token,)
        )
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user



@app.post("/create_user")
async def register(user: User, connection: aiosqlite.Connection = Depends(get_db)):
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
        db_user = await cursor.fetchone()
        if db_user:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "User with this email exists")

        hashed_pwd = hash_password(user.password.get_secret_value())
        websocket_token = str(uuid.uuid4())

        await cursor.execute(
            "INSERT INTO users (email, password, websocket_token) VALUES (?, ?, ?)",
            (user.email, hashed_pwd, websocket_token)
        )
        await connection.commit()

    return {"message": "User created successfully", "websocket_token": websocket_token}


@app.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    connection: aiosqlite.Connection = Depends(get_db),
):
    async with connection.cursor() as cursor:
        await cursor.execute("SELECT * FROM users WHERE email = ?", (form_data.username,))
        user = await cursor.fetchone()

    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User not found")

    if not check_password(form_data.password, user["password"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect password")

    return {
        "access_token": user["websocket_token"],
        "token_type": "bearer"
    }


@app.get("/")
async def get(request: Request):
    return templates.TemplateResponse("websocket.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def ws(websocket: WebSocket, client_id: int, connection: aiosqlite.Connection = Depends(get_db)):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        raise HTTPException(status_code=404, detail="not websocket token")

    async with connection.cursor() as cursor:
        await cursor.execute("SELECT * FROM users WHERE websocket_token = ?", (token,))
        user = await cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="no user")

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Клієнт #{client_id} написав: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Клієнт #{client_id} вийшов з чату")


if __name__ == "__main__":
    uvicorn.run("websocketHW:app", reload=True, port=8000)