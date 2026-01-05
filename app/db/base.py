from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.models import Base

# Création du moteur
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Création de l'usine à sessions
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    """Crée les tables si elles n'existent pas"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dépendance pour avoir la DB dans les routes
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session