from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from loguru import logger

from app.db.base import get_db
from app.db.models import Item, AuditLog
from app.automation.playwright_agent import VintedAgent
from app.core.discord import send_discord_alert
from app.ml.pricing import calculate_profit

router = APIRouter()
agent = VintedAgent()

class SnipeRequest(BaseModel):
    keyword: str
    max_price: float

@router.post("/scan")
async def scan_market(request: SnipeRequest, db: AsyncSession = Depends(get_db)):
    """
    Scan manuel via API. 
    Effectue une recherche, analyse le profit et envoie des alertes.
    """
    logger.info(f"🚀 Scan manuel demandé : {request.keyword} (Max: {request.max_price}€)")
    
    if not agent.browser:
        await agent.start()

    try:
        items_found = await agent.search(request.keyword, request.max_price)
        
        saved_count = 0
        alerts_sent = 0

        for item_data in items_found:
            # Vérification doublon
            stmt = select(Item).where(Item.vinted_id == item_data["vinted_id"])
            result = await db.execute(stmt)
            if result.scalars().first():
                continue

            # Analyse Élite
            item_data["real_details"] = await agent.get_real_details(item_data['url'])
            market_avg = await agent.analyze_market_price(item_data['raw_title'], item_data['vinted_id'])
            item_data["analysis"] = calculate_profit(item_data["price"], market_avg)

            # Sauvegarde en base
            new_item = Item(
                vinted_id=item_data["vinted_id"],
                title=item_data["raw_title"],
                price=item_data["price"],
                brand=item_data["brand"],
                size=item_data["size"],
                url=item_data["url"],
                photo_url=item_data.get("photo_url", "")
            )
            db.add(new_item)
            saved_count += 1
            
            # Alerte Discord
            await send_discord_alert(item_data)
            alerts_sent += 1

        # Log d'audit
        log = AuditLog(action="MANUAL_SCAN", details=f"KW: {request.keyword} | Found: {len(items_found)} | Notified: {alerts_sent}")
        db.add(log)
        await db.commit()
        
        return {
            "status": "success",
            "results_found": len(items_found),
            "new_items_saved": saved_count,
            "alerts_sent": alerts_sent
        }

    except Exception as e:
        logger.error(f"❌ Erreur lors du scan manuel : {e}")
        raise HTTPException(status_code=500, detail=str(e))
