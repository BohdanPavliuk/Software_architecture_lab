from fastapi import FastAPI
import json

app = FastAPI()

with open("config.json", "r") as f:
    service_registry = json.load(f)

@app.get("/services/{service_name}")
async def get_service_instances(service_name: str):
    instances = service_registry.get(service_name)
    if instances:
        return {"instances": instances}
    return {"instances": []}
