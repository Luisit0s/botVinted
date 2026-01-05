from fastapi import FastAPI
from contextlib import asynccontextmanager
from loguru import logger

from app.api.routes import router
from app.db.base import init_db
from app.core.scheduler import start_scheduler, agent as vinted_agent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    logger.info("🔥 Initialisation du Vinted Monster...")
    await init_db()
    await start_scheduler()
    yield
    # --- SHUTDOWN ---
    logger.info("🛑 Arrêt du système et fermeture du navigateur...")
    await vinted_agent.stop()

app = FastAPI(
    title="🏭 Vinted Monster Factory",
    version="2.0.0",
    lifespan=lifespan
)

# Inclusion des routes API
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def health_check():
    return {"status": "online", "message": "Vinted Monster is hunting..."}
