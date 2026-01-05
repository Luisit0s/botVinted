from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.models import Base

# Création du moteur asynchrone
engine = create_async_engine(
    settings.DATABASE_URL, 
    echo=False,  # Mets à True pour voir les requêtes SQL dans la console
    future=True
)

# Usine à sessions
AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db():
    """Crée les tables si elles n'existent pas."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Dépendance pour injecter la session DB dans les routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
