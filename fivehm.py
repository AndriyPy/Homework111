from fastapi import FastAPI, HTTPException, Path, Query, Header
import uvicorn
from datetime import datetime

app = FastAPI()

@app.post("/index/{user_id}")
async def index(
    user_id: int = Path(..., description="user id"),
    timestamp: datetime = Query(None, description="time"),
    X_Client_Version: str = Header(alias="X-Client-Version")
):
    if timestamp is None:
        timestampp = datetime.now()
        return {
            "user_id": user_id,
            "X-Client-Version": X_Client_Version,
            "timestamp": timestampp
        }

    return {
        "user_id": user_id,
        "X-Client-Version": X_Client_Version,
        "timestamp": timestamp
    }

if __name__ == "__main__":
    uvicorn.run("fivehm:app", reload=True)

import uvicorn
from datetime import datetime


app = FastAPI()


@app.post("/index/{user_id}")
async def index(user_id:int = Path(...,description="user id"),
                timestamp:datetime = Query(None, description="time"),
                X_Client_Version: str = Header(alias="X-Client-Version")):
    if timestamp is None:
        timestampp = datetime.now()
        return {"user_id":user_id, "X-Client-Version":X_Client_Version, "timestamp":timestampp}

    return {"user_id":user_id,
            "X-Client-Version":X_Client_Version,
            "timestamp":timestamp}


if __name__ == "__main__":
    uvicorn.run("fivehm:app", reload=True)
