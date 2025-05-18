from fastapi import FastAPI, Request
from hazelcast import HazelcastClient
import os

app = FastAPI()
hz = HazelcastClient(cluster_members=[os.getenv("HZ_HOST", "hazelcast1:5701")])
log_map = hz.get_map("logs").blocking()

@app.post("/log")
async def add_log(request: Request):
    data = await request.json()
    key = data.get("key")
    value = data.get("value")
    log_map.put(key, value)
    print(f"Stored: {key} -> {value}")
    return {"status": "ok"}

@app.get("/log/{key}")
async def get_log(key: str):
    value = log_map.get(key)
    print(f"Retrieved: {key} -> {value}")
    return {"key": key, "value": value}
