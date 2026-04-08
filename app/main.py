from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import bakes, adviser

app = FastAPI(title="Sourdough Adviser", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this later when you have a stable frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bakes.router, prefix="/bakes", tags=["bakes"])
app.include_router(adviser.router, prefix="/adviser", tags=["adviser"])

@app.get("/health")
def health():
    return {"status": "ok"}