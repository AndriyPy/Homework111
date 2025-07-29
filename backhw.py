from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Path, status
from pydantic import BaseModel, Field, EmailStr
import uvicorn
import asyncio
import logging
import pytest
import httpx


task_queue = asyncio.Queue()

async def process_task_queue():
    while True:
        task = await task_queue.get()

        try:
            await task
        except Exception as e:
            print(f"Error {e}")
        else:
            task_queue.task_done()
        if task_queue.empty():
            print("All tasks have been completed.")

async def startup_event():
    asyncio.create_task(process_task_queue())

async def image(file: UploadFile):
    file_size = Path(file).stat().st_size
    logger.info(f"size: {file_size}")


app = FastAPI( on_startup=(startup_event,))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def write_message(email: str, message: str):
    await asyncio.sleep(1)
    logger.info(f"Sent message to {email} with text: {message}")

class Email(BaseModel):
    email: EmailStr = Field(description="write your email")
    text: str = Field(description="write email text")

@app.post("/post_email")
async def post_email(user_email: Email, backgroundtasks: BackgroundTasks):
    logger.info(f"Request received to send message to: {user_email.email}")
    backgroundtasks.add_task(write_message, user_email.email, user_email.text)
    return {"message": f"request to send a letter accepted {user_email.email}"}


@app.post("/post_file")
async def upload_file(backgroundtasks: BackgroundTasks, file: UploadFile = File(...)):
    path = "picture_from_bytes.jpeg"

    contents = await file.read()

    with open(path, "wb") as fp:
        fp.write(contents)

    backgroundtasks.add_task(image, path)

    logger.info("file was written")
    return {"file_size": len(contents)}



@pytest.mark.asyncio
async def test_send_email() -> None:
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        response = await client.post(
            "/post_email",
            json={"email": "name@gmail.com", "text": "Some text"},
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "message": "request to send a letter accepted name@gmail.com"
    }



if __name__ == "__main__":
    uvicorn.run("backhw:app", reload=True)
