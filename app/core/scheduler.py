import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from sqlalchemy import delete
from loguru import logger

from app.db.base import AsyncSessionLocal
from app.automation.playwright_agent import VintedAgent
from app.core.discord import send_discord_alert
from app.db.models import Item
from app.ml.pricing import calculate_profit 

# ==========================================
# 🎯 TES CIBLES (LISTE COMPLÈTE)
# ==========================================
TARGETS = [
    {"keyword": "Corteiz", "max_buy_price": 60, "webhook": "https://discord.com/api/webhooks/1446121642844749884/EHfuqbN0-DA88tOMGzZkOeCzDLn-Bfsc98DFj9wRfrQ2on9sYkd66t3kvXCSt4zyN8wU"},
    {"keyword": "Stussy", "max_buy_price": 50, "webhook": "https://discord.com/api/webhooks/1446121862470832169/g2Yzxxzmakm0LR5gMBHCWSFgsVNNzNQKCETLZTIUwF7xYqPeAq_pCX5pl3mQAAjzThlu"},
    {"keyword": "Supreme", "max_buy_price": 50, "webhook": "https://discord.com/api/webhooks/1446122085276586095/BzZttmy4185HfFbGTt7tJMw1ypglG3UVbGr84mjIsBfhqUN3cw3fRPVPi1xivjdkKlh3"},
    {"keyword": "Carhartt WIP", "max_buy_price": 40, "webhook": "https://discord.com/api/webhooks/1446122775000387584/PSsYsBNQfKazZajO_X7fLWmCqCM7AHdj-dwDd8QlnD9R_LhC0BFAxwzGem1PeZdp93aq"},
    {"keyword": "Project X Paris", "max_buy_price": 25, "webhook": "https://discord.com/api/webhooks/1446134854126141516/cJcMmPBAt6kfjguwrAYmFHfZIRGNMRiAZ1oxmkRDucTqgLT3Dw2p4k-w3y6mgtmrAmwa"},
    {"keyword": "Arcteryx", "max_buy_price": 120, "webhook": "https://discord.com/api/webhooks/1446122992756199527/LXGcYtgpJUIniEmYhE-Xg212f6yN7ki9gn6bazQcI1YtkQE_DEN4TuZFC1FMuJ6mfWMd"},
    {"keyword": "The North Face", "max_buy_price": 60, "webhook": "https://discord.com/api/webhooks/1446123210830647310/jV3wrsdshh76-qT6wkFZ5NdEkaesq8W4MzGa-vBCIToEBUwwgofE65fiTJwROIkqCa4nN"},
    {"keyword": "Salomon", "max_buy_price": 65, "webhook": "https://discord.com/api/webhooks/1446123494684364810/CI_qo6JT_gEM8pdQi46uYo8-6XZcHCtLiY97aWAqkI9wq8pTafuVfbCTqT_mQnVet2OZ"},
    {"keyword": "Stone Island", "max_buy_price": 90, "webhook": "https://discord.com/api/webhooks/1446125928777383956/GyiEzFaPIUztO4OwybNP3kd2a_Wi0q7olry95cQRLI-6TET6nMhFnwnryFuKYQabUsWP"},
    {"keyword": "Ralph Lauren", "max_buy_price": 30, "webhook": "https://discord.com/api/webhooks/1446126468349300777/7S5lMvuwAnblXfo2euat7kDtKL_55YsJqIhLYm7Gsx_hCn9nlXc5BqMElwriHbtdG_zS"},
    {"keyword": "Lacoste", "max_buy_price": 35, "webhook": "https://discord.com/api/webhooks/1446126842850447475/WkH6Ptc1zFeyjW2DRu3FzQDhHX48UsXGQw5TJvoREy3zSLArvkkxVTqYjba4Vm-FrWOC"},
    {"keyword": "Jacquemus", "max_buy_price": 100, "webhook": "https://discord.com/api/webhooks/1446127351225122940/DfdoQvv1b2wt82PvLCBuGmg1TqdBNbOB_sXBML--PoaivAhU4dJwZDJyCKjI86r50HOR"},
    {"keyword": "Zadig Voltaire", "max_buy_price": 70, "webhook": "https://discord.com/api/webhooks/1446135404154847313/cqidHXwp6GY6EREEdfw2T1uImZtz9EOldbweFamTiWXs3ogKihvPP5v9ZFvXrLQy8Rk2"},
    {"keyword": "Dr Martens", "max_buy_price": 60, "webhook": "https://discord.com/api/webhooks/1446128233228668939/gJQriyxrBoRBwCrneqBWTuc4-1tT1nUq3s-Uoz9ur7eot45bmOthYbdQBCk3D0d21HSI"},
    {"keyword": "levis 501", "max_buy_price": 30, "webhook": "https://discord.com/api/webhooks/1446134079035805808/FNdgoqY7hQ-IP_32pPHh7Tpve-92MgJl79guhI-9yUn1kgqZyj5stNWHoVfKsJ_HG3HW"}
]

# ==========================================
# 🛑 FILTRES DE SÉCURITÉ
# ==========================================
CONDITIONS_ACCEPTEES = ["neuf", "neuf avec étiquette", "neuf sans étiquette", "très bon état", "bon état"]
BLACKLIST_KEYWORDS = [
    "je recherche", "je cherche", "recherche", "fausse", "faux", "fake", "contrefaçon", 
    "concours", "gagner", "tirage", "sort", "participation", "insta", "instagram", 
    "règlement", "infos", "giveaway", "lot", "ticket", "abonné", "conditions"
]

agent = VintedAgent()
scheduler = AsyncIOScheduler()

async def job_cleanup_db():
    """🧹 Supprime les anciens articles pour garder une DB légère."""
    logger.info("🧹 Nettoyage DB (Articles > 48h)...")
    cutoff_date = datetime.utcnow() - timedelta(hours=48)
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Item).where(Item.created_at < cutoff_date))
            await db.commit()
    except Exception as e:
        logger.error(f"❌ Erreur lors du nettoyage DB : {e}")

async def job_scan_market():
    """🕵️‍♂️ Cœur du bot : Scanne chaque cible de manière isolée."""
    logger.info("🕵️‍♂️ Scan STRATÉGIQUE lancé...")
    if not agent.browser: await agent.start()

    for target in TARGETS:
        try:
            keyword = target["keyword"]
            max_buy = target["max_buy_price"]
            webhook = target.get("webhook")
            
            if not webhook or "METS_TON_LIEN" in webhook: continue

            # Pause humaine entre les recherches
            await agent.random_sleep(1.0, 3.0)
            
            items_found = await agent.search(keyword, max_buy)
            
            async with AsyncSessionLocal() as db:
                for item_data in items_found:
                    # 1. Filtre État
                    etat = str(item_data.get("condition", "")).lower().strip()
                    if etat not in CONDITIONS_ACCEPTEES: continue

                    # 2. Filtre Anti-Spam / Concours
                    title_lower = item_data['raw_title'].lower()
                    if any(bad in title_lower for bad in BLACKLIST_KEYWORDS):
                        continue

                    # 3. Anti-Doublon
                    res = await db.execute(select(Item).where(Item.vinted_id == item_data["vinted_id"]))
                    if res.scalars().first(): continue

                    # 4. Enrichissement des données
                    logger.info(f"🔎 Analyse du deal : {item_data['raw_title']} à {item_data['price']}€")
                    
                    item_data["real_details"] = await agent.get_real_details(item_data['url'])
                    market_avg = await agent.analyze_market_price(item_data['raw_title'], item_data['vinted_id'])
                    item_data["analysis"] = calculate_profit(item_data["price"], market_avg)

                    # 5. Sauvegarde
                    new_item = Item(
                        vinted_id=item_data["vinted_id"],
                        title=item_data["raw_title"],
                        price=item_data["price"],
                        brand=item_data["brand"],
                        size=item_data["size"],
                        url=item_data["url"],
                        photo_url=item_data.get("photo_url", ""),
                        created_at=datetime.utcnow()
                    )
                    db.add(new_item)
                    await db.commit()
                    
                    # 6. Alerte 🚀
                    logger.success(f"✅ Alerte envoyée pour : {item_data['raw_title']}")
                    await send_discord_alert(item_data, webhook_url=webhook)
                    
                    await asyncio.sleep(1) # Petit délai pour Discord

        except Exception as e:
            logger.error(f"❌ Erreur lors du scan pour '{target.get('keyword')}': {e}")
            continue

async def start_scheduler():
    """🚀 Initialise et démarre les tâches automatiques."""
    await agent.start()
    
    # Scan toutes les 3 minutes (180s)
    scheduler.add_job(job_scan_market, 'interval', seconds=180)
    # Nettoyage DB toutes les 24h
    scheduler.add_job(job_cleanup_db, 'interval', hours=24)
    
    scheduler.start()
    logger.success("🚀 Monster Scheduler 2.0 en ligne !")
    
    # Lancement immédiat du premier scan
    asyncio.create_task(job_scan_market())
