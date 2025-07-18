from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import logging
from datetime import datetime

app = FastAPI()

logger = logging.getLogger("middleware_logger")
logging.basicConfig(level=logging.INFO)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"request_method: {request.method}, url: {request.url}, time: {datetime.now()}")

    if "X-Custom-Header" not in request.headers:
        return JSONResponse(status_code=400, content="Missing X-Custom-Header")

    response = await call_next(request)
    return response


@app.get("/")
async def root(request: Request):
    return {
        "message": "main page",
        "X-Custom-Header": request.headers["X-Custom-Header"],
    }

@app.get("/second")
async def public_page():
    return {"message": "second"}


if __name__ == "__main__":
    uvicorn.run("middlewareHW:app", reload=True)