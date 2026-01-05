import httpx
from datetime import datetime
from loguru import logger
from app.core.config import settings

async def send_discord_alert(item: dict, webhook_url: str = None):
    """
    Envoie une notification Discord Élite.
    Design optimisé pour la revente (Resell).
    """
    target_url = webhook_url or settings.DISCORD_WEBHOOK_URL
    if not target_url:
        logger.error("❌ Aucun Webhook Discord configuré.")
        return

    # Récupération sécurisée des données
    prix = item.get('price', 0)
    ttc = prix + 0.70 + (prix * 0.05)
    
    details = item.get("real_details", {})
    date_publi = details.get("time", "À l'instant")
    avis = details.get("rating", "N/A")
    reviews = details.get("review_count", "0")
    
    analysis = item.get("analysis", {})
    profit = analysis.get("profit", 0)
    roi = analysis.get("roi", 0)

    # Style visuel
    color = 0x2B2D31 # Gris sombre Premium
    if roi > 40: color = 0x2ECC71 # Vert si très rentable
    
    embed = {
        "color": color,
        "author": {
            "name": "VINTED MONSTER • HIGH SPEED SCAN",
            "icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Vinted_logo.png/600px-Vinted_logo.png"
        },
        "title": f"🔥 {item.get('raw_title', 'Article sans titre')}",
        "url": item.get('url', ''),
        "description": f"✨ **Nouveau deal trouvé !**\n\n📄 **[Détails de l'annonce]({item.get('url', '')})**\n💳 **[Achat Rapide]({item.get('url', '')})**",
        "image": {"url": item.get("photo_url", "")},
        "fields": [
            {"name": "💰 Prix", "value": f"**{prix}€** (TTC: {round(ttc, 2)}€)", "inline": True},
            {"name": "📈 Profit Est.", "value": f"**+{profit}€** ({roi}%)", "inline": True},
            {"name": "📏 Taille", "value": item.get('size', 'N/A'), "inline": True},
            {"name": "🏷️ Marque", "value": item.get('brand', 'Inconnu'), "inline": True},
            {"name": "🌟 Avis Vendeur", "value": f"{avis} ({reviews})", "inline": True},
            {"name": "⌛ Publié", "value": date_publi, "inline": True}
        ],
        "footer": {
            "text": f"Vinted Monster v2.0 • {datetime.now().strftime('%H:%M:%S')}",
            "icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Vinted_logo.png/600px-Vinted_logo.png"
        }
    }

    payload = {
        "username": "Vinted Monster",
        "avatar_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Vinted_logo.png/600px-Vinted_logo.png",
        "embeds": [embed]
    }

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(target_url, json=payload)
            r.raise_for_status()
        except Exception as e:
            logger.error(f"❌ Échec de l'envoi Discord : {e}")
