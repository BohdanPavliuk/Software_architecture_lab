from fastapi import FastAPI, Request
from pydantic import BaseModel
import uuid
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, RetryError

app = FastAPI()

LOGGING_URL = "http://logging_service:8000/logging_service"
MESSAGE_URL = "http://messages_service:8000/messages_service"

class Msg(BaseModel):
    msg: str

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type(httpx.RequestError)
)
async def send_to_logging(payload):
    async with httpx.AsyncClient() as client:
        await client.post(LOGGING_URL, json=payload)

@app.post("/fassade_service")
async def send_msg(data: Msg):
    msg_id = str(uuid.uuid4())
    payload = {"uuid": msg_id, "msg": data.msg}
    try:
        await send_to_logging(payload)
        return {"uuid": msg_id, "status": "sent"}
    except RetryError as e:
        print(f"[ERROR] Failed to reach logging-service after retries: {e}")
        return {"uuid": msg_id, "status": "failed", "error": "logging-service unreachable after retries"}

@app.get("/fassade_service")
async def get_combined():
    logs = []
    static_msg = "unavailable"

    async with httpx.AsyncClient() as client:
        try:
            logs_resp = await client.get(LOGGING_URL)
            logs = logs_resp.json().get("logs", [])
        except httpx.RequestError as e:
            print(f"[ERROR] Could not reach logging_service: {e}")
            logs = ["<logging unavailable>"]
        try:
            msg_resp = await client.get(MESSAGE_URL)
            static_msg = msg_resp.json().get("message", "unavailable")
        except httpx.RequestError as e:
            print(f"[ERROR] Could not reach message_service: {e}")
            static_msg = "<message unavailable>"

    result_str = f"{logs} : {static_msg}"
    return {"result": result_str}