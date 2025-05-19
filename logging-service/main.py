import os
import socket
from uuid import uuid4
from fastapi import FastAPI, Request
import hazelcast
import consul

app = FastAPI()


INSTANCE_ID = os.getenv("INSTANCE_ID", "unknown")
SERVICE_NAME = "logging-service"
PORT = 8000 


def get_consul_client():
    return consul.Consul(host=os.getenv("CONSUL_HOST", "consul"), port=8500)

def get_consul_kv(key: str):
    c = get_consul_client()
    _, data = c.kv.get(key)
    if data and data["Value"]:
        return data["Value"].decode()
    return None

def register_to_consul():
    c = get_consul_client()
    ip = socket.gethostbyname(socket.gethostname())
    c.agent.service.register(
        name=SERVICE_NAME,
        service_id=f"{SERVICE_NAME}-{INSTANCE_ID}",
        address=ip,
        port=PORT,
        tags=["fastapi", "hazelcast"],
        check=consul.Check.http(f"http://{ip}:{PORT}/health", interval="10s")
    )


hz_members = get_consul_kv("hz/cluster_members")
hz_cluster = hz_members.split(",") if hz_members else ["hazelcast1:5701"]

hz = hazelcast.HazelcastClient(cluster_members=hz_cluster)
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

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def startup():
    print(f"[LogSvc {INSTANCE_ID}] Registering to Consul...")
    register_to_consul()
