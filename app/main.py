from fastapi import FastAPI
from app.routes import bakes, adviser

app = FastAPI()
app.include(bakes.router, prefix="/bakes")
app.include(adviser.router, prefix="/adviser")