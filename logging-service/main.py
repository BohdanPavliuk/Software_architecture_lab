import os
from fastapi import FastAPI, Request
import hazelcast
from uuid import uuid4

app = FastAPI()
INSTANCE_ID = os.getenv("INSTANCE_ID", "unknown")

hz = hazelcast.HazelcastClient(
    cluster_members=["hazelcast1:5701", "hazelcast2:5701", "hazelcast3:5701"]
)
log_map = hz.get_map("log-map").blocking()

@app.post("/log")
async def log_message(request: Request):
    data = await request.json()
    msg = data.get("msg", "unknown")

    log_id = str(uuid4())
    log_entry = f"[LogSvc {INSTANCE_ID}] {msg}"
    log_map.set(log_id, log_entry) 
    print(log_entry)

    return {"status": "logged", "msg": msg, "id": log_id}

@app.get("/logs")
def get_logs():
    entries = log_map.entry_set()
    return {"logs": [value for key, value in entries]}
