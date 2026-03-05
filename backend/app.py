from fastapi import FastAPI

from backend.apis.routes.job_api import job_router
from backend.apis.routes.user_api import user_router

app = FastAPI(title="JournalismJobForge", version="0.0.1")

app.include_router(job_router, prefix="")
app.include_router(user_router, prefix="")

@app.get("/")
def home():
    return {"message": "ok"}
