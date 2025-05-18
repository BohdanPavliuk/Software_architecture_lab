from fastapi import FastAPI
import hazelcast, threading, os
import time

app = FastAPI()
INSTANCE_ID = os.getenv("INSTANCE_ID", "unknown")
hz = hazelcast.HazelcastClient(cluster_members=["hazelcast1:5701", "hazelcast2:5701", "hazelcast3:5701"])
queue = hz.get_queue("msg-queue").blocking()
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
    threading.Thread(target=consume_loop, daemon=True).start()

@app.get("/messages")
def get_stored():
    return stored


@app.get("/debug/queue_size")
def get_queue_size():
    return {"size": queue.size()}
