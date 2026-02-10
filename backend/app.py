from fastapi import FastAPI

from backend.apis.routes import router

app = FastAPI(title="JournalismJobForge", version="0.0.1")
app.include_router(router, prefix="/")

@app.get("/")
def home():
    return {"message": "ok"}
