from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
import uvicorn
from PIL import Image
import io
import pytest


app = FastAPI()
client = TestClient(app)

MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}
SAVE_PATH = "converted_image.jpg"


async def edit_format(contents: bytes, path: str):
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    output = io.BytesIO()
    image.save(output, format="JPEG")
    output.seek(0)

    with open(path, "wb") as f:
        f.write(output.read())

@app.post("/photo")
async def photo(backgroundtasks: BackgroundTasks, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="format doesn't exist")

    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="file is too big")

    backgroundtasks.add_task(edit_format, contents, SAVE_PATH)

    return JSONResponse({
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(contents),
        "message": f"Файл буде збережений як {SAVE_PATH}"
    })


def test_upload_file_success() -> None:
    with open("test_file_supported_format.jpg", "rb") as f:
        expected_size = len(f.read())
        f.seek(0)
        response = client.post(
            "/photo",
            files={"file": f},
        )

    assert response.status_code == 200
    assert response.json() == {
        "filename": "test_file_supported_format.jpg",
        "content_type": "image/jpeg",
        "size": expected_size,
        "message": f"Файл буде збережений як {SAVE_PATH}",
    }


def test_upload_file_not_supported_format() -> None:
    with open("test_file_unsupported_format.webp", "rb") as f:
        response = client.post(
            "/photo",
            files={"file": f},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "format doesn't exist"}


if __name__ == "__main__":
    uvicorn.run("filehw:app", reload=True, port=1488)
