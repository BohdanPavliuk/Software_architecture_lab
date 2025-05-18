from fastapi import FastAPI, Request
import httpx, random, os

app = FastAPI()

CONFIG_SERVER = os.getenv("CONFIG_SERVER", "http://config-server:8500")

async def get_service_instances(service_name: str):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{CONFIG_SERVER}/services/{service_name}")
            return resp.json().get("instances", [])
        except Exception as e:
            print(f"Error getting services: {e}")
            return []

async def try_request(method, service_name, url, **kwargs):
    instances = await get_service_instances(service_name)
    random.shuffle(instances)
    for instance in instances:
        try:
            async with httpx.AsyncClient() as client:
                response = await getattr(client, method)(f"{instance}{url}", **kwargs)
                return response.json()
        except Exception as e:
            print(f"Failed on {instance}: {e}")
    return {"error": "All instances failed"}

@app.post("/log")
async def proxy_post(req: Request):
    data = await req.json()
    return await try_request("post", "logging-service", "/log", json=data)

@app.get("/log/{key}")
async def proxy_get(key: str):
    return await try_request("get", "logging-service", f"/log/{key}")
