from fastapi import FastAPI

app = FastAPI()

@app.get("/messages_service")
def get_message():
    return {"message": "not implemented yet"}
