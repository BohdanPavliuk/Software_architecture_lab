from fastapi import FastAPI
import hazelcast, threading, os, time, socket
import consul

app = FastAPI()


INSTANCE_ID = os.getenv("INSTANCE_ID", "unknown")
SERVICE_NAME = "messages-service"
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
        tags=["consumer"],
        check=consul.Check.http(f"http://{ip}:{PORT}/health", interval="10s")
    )


hz_members = get_consul_kv("hz/cluster_members")
hz_cluster = hz_members.split(",") if hz_members else ["hazelcast1:5701"]
queue_name = get_consul_kv("hz/queue_name") or "msg-queue"


hz = hazelcast.HazelcastClient(cluster_members=hz_cluster)
queue = hz.get_queue(queue_name).blocking()
stored = []


def consume_loop():
    print(f"[MsgSvc {INSTANCE_ID}] Consumer loop running.")
    time.sleep(2)
    while True:
        try:
            msg = queue.take()
            print(f"[MsgSvc {INSTANCE_ID}] Consumed: {msg}")
            stored.append(msg)
        except Exception as e:
            print(f"[MsgSvc {INSTANCE_ID}] Error: {e}")

@app.on_event("startup")
def startup_event():
    print(f"[MsgSvc {INSTANCE_ID}] Registering to Consul...")
    register_to_consul()
    threading.Thread(target=consume_loop, daemon=True).start()

@app.get("/messages")
def get_stored():
    return stored

@app.get("/debug/queue_size")
def get_queue_size():
    return {"size": queue.size()}

@app.get("/health")
def health_check():
    return {"status": "ok"}
