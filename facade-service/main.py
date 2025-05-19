import os
import socket
import random
from fastapi import FastAPI, Request
import hazelcast
import httpx
import consul

app = FastAPI()

# --- Service Identity ---
INSTANCE_ID = os.getenv("INSTANCE_ID", "unknown")
SERVICE_NAME = "facade-service"
PORT = 8000

# --- Consul client ---
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
        tags=["fastapi"],
        check=consul.Check.http(f"http://{ip}:{PORT}/health", interval="10s")
    )

def discover_service(service_name):
    c = get_consul_client()
    _, nodes = c.health.service(service_name, passing=True)
    if not nodes:
        return None
    return random.choice(nodes)["Service"]

# --- Load Hazelcast and Queue config from Consul ---
hz_members = get_consul_kv("hz/cluster_members")
hz_cluster = hz_members.split(",") if hz_members else ["hazelcast1:5701"]
queue_name = get_consul_kv("hz/queue_name") or "msg-queue"

hz = hazelcast.HazelcastClient(cluster_members=hz_cluster)
queue = hz.get_queue(queue_name).blocking()

@app.post("/message")
async def post_message(request: Request):
    data = await request.json()
    msg = data.get("msg")
    queue.put(msg)

    # Discover logging-service
    log_svc = discover_service("logging-service")
    if log_svc:
        logging_url = f"http://{log_svc['Address']}:{log_svc['Port']}/log"
        try:
            async with httpx.AsyncClient() as client:
                await client.post(logging_url, json={"msg": msg})
        except Exception as e:
            print(f"Failed to log to {logging_url}: {e}")
    else:
        print("No healthy logging-service found")

    return {"status": "added", "msg": msg}

@app.get("/messages")
async def get_messages():
    msg_svc = discover_service("messages-service")
    log_svc = discover_service("logging-service")

    if not msg_svc or not log_svc:
        return {"error": "No available services"}

    messages_url = f"http://{msg_svc['Address']}:{msg_svc['Port']}/messages"
    logging_url = f"http://{log_svc['Address']}:{log_svc['Port']}/logs"

    async with httpx.AsyncClient() as client:
        try:
            msg_resp = await client.get(messages_url)
            log_resp = await client.get(logging_url)
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

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def startup():
    print(f"[Facade {INSTANCE_ID}] Registering to Consul...")
    register_to_consul()
