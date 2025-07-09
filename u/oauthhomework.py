import uvicorn
import aiosqlite
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import (
    HTTPBasic,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    HTTPBasicCredentials
)
from pydantic import BaseModel, EmailStr, SecretStr, Field
import base64



app = FastAPI(description="API with OAuth2 and HTTP Basic",)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
security = HTTPBasic()


users = {
    "andrii": {
        "name": "andrii",
        "email": "qqq@gmail.com",
        "password": "123456",
    }
}

class Token(BaseModel):

    token_type: str = Field(description="type of the token", examples=["bearer"])
    access_token: str = Field(description="token value", examples=["#3HM4J24V324kljn2"])

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: SecretStr


class UserShow(UserCreate):
    id: int
    is_active: bool = False

@app.post("/token",
          response_model=Token,
          tags=["auth"],
          summary="Get access token by promided email and password",
          description="Endpoind for auth purpose",
          responses={
              200:{"description":"Success"},
              404: {"Description":"User not found"},
              400:{"Description":"Incorrect password"}
          },
          operation_id="get-access-token",
          include_in_schema=True,
          name="get_token")
async def login( form_data: OAuth2PasswordRequestForm = Depends(),):
    if users is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User does not exist.")

    user_data = users.get(form_data.username)
    if user_data:
        if user_data["password"] != form_data.password:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Incorrect password.")

    token_value = base64.urlsafe_b64encode(
        f"{user_data['email']}-{user_data['name']}".encode("utf-8")
    ).decode("utf-8")

    return Token(access_token=token_value, token_type="bearer")

async def decode_token(token: str):
    try:

        decoded_user_email = (
            base64.urlsafe_b64decode(token).split(b"-")[0].decode("utf-8")
        )
    except (UnicodeDecodeError, ValueError):
        return None

    return decoded_user_email

@app.get("/me", summary="Отримати інформацію про користувача",
         description="Повертає email та ім'я користувача на основі переданого access токена.",
         responses={
             200: {"description": "Інформація про користувача"},
             401: {"description": "Невірний або недійсний токен"},
             404: {"description": "Користувача не знайдено"},})
async def get_user_me(token: str = Depends(oauth2_scheme)):
    email = await decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")

    for user in users.values():
        if user["email"] == email:
            return {"email": email, "name": user["name"]}

    raise HTTPException(status_code=404, detail="User not found")



@app.post("/basic",
    summary="HTTP Basic авторизація",
    description="Авторизація через стандартний HTTP Basic",
    responses={
        200: {"description": "Успішний логін"},
        401: {"description": "Невірні дані"},
    })
async def basic(credentials: HTTPBasicCredentials = Depends(security)):
    user = users.get(credentials.username)
    if not user or user["password"] != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return {"message": f"Hello, {credentials.username}!"}



if __name__ == "__main__":
    uvicorn.run("oauthhomework:app", reload=True)