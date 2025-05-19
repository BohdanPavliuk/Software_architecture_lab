from fastapi import FastAPI, Request
import hazelcast
import httpx
import random

app = FastAPI()

hz = hazelcast.HazelcastClient(
    cluster_members=["hazelcast1:5701", "hazelcast2:5701", "hazelcast3:5701"]
)
queue = hz.get_queue("msg-queue").blocking()

MESSAGES_SERVICES = ["http://messages1:8000", "http://messages2:8000"]
LOGGING_SERVICES = ["http://logging1:8000", "http://logging2:8000", "http://logging3:8000"]

@app.post("/message")
async def post_message(request: Request):
    data = await request.json()
    msg = data.get("msg")
    queue.put(msg)

    logging_url = random.choice(LOGGING_SERVICES)
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{logging_url}/log", json={"msg": msg})
    except Exception as e:
        print(f"Failed to log to {logging_url}: {e}")

    return {"status": "added", "msg": msg}

@app.get("/messages")
async def get_messages():
    messages_url = random.choice(MESSAGES_SERVICES)
    logging_url = random.choice(LOGGING_SERVICES)

    async with httpx.AsyncClient() as client:
        try:
            msg_resp = await client.get(f"{messages_url}/messages")
            log_resp = await client.get(f"{logging_url}/logs")
        except Exception as e:
            return {"error": str(e)}

    return {
        "from": {
            "messages_service": messages_url,
            "logging_service": logging_url
        },
        "messages": {
            "stored": msg_resp.json(),
            "logs": log_resp.json().get("logs", [])
        }
    }

