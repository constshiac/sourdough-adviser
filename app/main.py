from fastapi import FastAPI
from app.routes import bakes, adviser

app = FastAPI(title="Sourdough Adviser", version="1.0.0")

app.include_router(bakes.router, prefix="/bakes", tags=["bakes"])
app.include_router(adviser.router, prefix="/adviser", tags=["adviser"])


@app.get("/health")
def health():
    return {"status": "ok"}