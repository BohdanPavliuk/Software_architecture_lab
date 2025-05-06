from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
logs = {}

class LogMessage(BaseModel):
    uuid: str
    msg: str

@app.post("/logging_service")
async def log_message(data: LogMessage):
    if data.uuid in logs:
        print(f"[SKIP - DUPLICATE] {data.uuid}")
        return {"status": "duplicate"}
    logs[data.uuid] = data.msg
    print(f"[LOGGED] {data.uuid}: {data.msg}")
    return {"status": "logged"}

@app.get("/logging_service")
async def get_logs():
    return {"logs": list(logs.values())}
