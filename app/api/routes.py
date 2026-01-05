from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.db.models import Item, AuditLog
from app.automation.playwright_agent import VintedAgent
# 👇 NOUVEL IMPORT
from app.core.discord import send_discord_alert

router = APIRouter()
agent = VintedAgent()

class SnipeRequest(BaseModel):
    keyword: str
    max_price: float

@router.on_event("startup")
async def startup():
    await agent.start()

@router.post("/scan")
async def scan_market(request: SnipeRequest, db: AsyncSession = Depends(get_db)):
    """Scan le marché, sauvegarde et NOTIFIE"""
    
    items_found = await agent.search(request.keyword, request.max_price)
    
    saved_count = 0
    notified_count = 0

    for item_data in items_found:
        # (Ici on simplifie : on considère que tout ce qu'on trouve est nouveau pour le test)
        # Dans le futur, on vérifiera si ça existe déjà en base pour ne pas spammer
        
        new_item = Item(
            title=item_data["raw_title"],
            price=item_data["price"],
            brand=item_data["brand"],
            size=item_data["size"],
            url=item_data["url"]
        )
        db.add(new_item)
        saved_count += 1
        
        # 🔔 C'EST ICI QUE CA SE PASSE
        # On envoie l'alerte Discord
        await send_discord_alert(item_data)
        notified_count += 1
    
    # Log
    log = AuditLog(action="SCAN", details=f"Keyword: {request.keyword} | Found: {len(items_found)}")
    db.add(log)
    await db.commit()
    
    return {
        "status": "success", 
        "scanned": len(items_found), 
        "saved": saved_count,
        "alerts_sent": notified_count,
        "data": items_found
    }