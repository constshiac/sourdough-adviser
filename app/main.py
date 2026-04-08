import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("=== Starting import of routes ===")

from fastapi import FastAPI

logger.info("FastAPI imported")

try:
    from app.routes import bakes
    logger.info("bakes router imported successfully")
except Exception as e:
    logger.error(f"FAILED to import bakes router: {e}", exc_info=True)

try:
    from app.routes import adviser
    logger.info("adviser router imported successfully")
except Exception as e:
    logger.error(f"FAILED to import adviser router: {e}", exc_info=True)

app = FastAPI(title="Sourdough Adviser", version="1.0.0")

app.include_router(bakes.router, prefix="/bakes", tags=["bakes"])
app.include_router(adviser.router, prefix="/adviser", tags=["adviser"])

@app.get("/health")
def health():
    return {"status": "ok"}

logger.info(f"=== Routes registered: {[r.path for r in app.routes]} ===")