from fastapi import FastAPI
from app.api.routes import router
from app.db.base import init_db
# 👇 Nouvel import
from app.core.scheduler import start_scheduler

app = FastAPI(title="🏭 Vinted Monster Factory")

app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def on_startup():
    # 1. On initialise la base de données
    await init_db()
    
    # 2. On lance le Cœur Automatique 💓
    await start_scheduler()