import httpx
from datetime import datetime
from loguru import logger
from app.core.config import settings

async def send_discord_alert(item: dict, webhook_url: str = None):
    """
    Envoie une notification Discord EXACTEMENT comme sur ton screen.
    Style: Vinted Plug / Monitor.
    """
    target_url = webhook_url or settings.DISCORD_WEBHOOK_URL
    if not target_url: return

    # 1. Calcul Prix TTC (Simple et efficace)
    # Formule : Prix + 0.70€ + 5%
    prix = item['price']
    frais = 0.70 + (prix * 0.05)
    prix_ttc = round(prix + frais, 2)

    # 2. Récupération des VRAIES infos (ou valeur par défaut si échec)
    real_details = item.get("real_details", {"time": "À l'instant", "rating": "N/A", "review_count": "0"})
    
    date_publi = real_details["time"]
    avis_stars = real_details["rating"]
    avis_count = real_details["review_count"]

    # Construction de la ligne Avis
    if avis_stars == "Nouveau":
        avis_display = "Nouveau Vendeur"
    else:
        avis_display = f"{avis_stars} ({avis_count})"

    # Couleur Bleu/Gris sombre style "Pro"
    color = 0x2B2D31 

    embed = {
        "color": color,
        
        "author": {
            "name": "Vinted Monster", 
            "icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/Vinted_logo.png/600px-Vinted_logo.png"
        },

        # Titre cliquable en bleu
        "title": item['raw_title'],
        "url": item['url'],
        
        # Liens rapides
        "description": f"📄 **[Détails]({item['url']})** • 💳 **[Acheter]({item['url']})** • 🤝 **[Négocier]({item['url']})**",
        
        # LA GRANDE IMAGE
        "image": {
            "url": item.get("photo_url", "")
        },
        
        "fields": [
            # LIGNE 1
            {
                "name": "⌛ Publiée",
                "value": date_publi, # VRAIE INFO
                "inline": True
            },
            {
                "name": "🏷️ Marque",
                "value": item['brand'],
                "inline": True
            },
            {
                "name": "📏 Taille",
                "value": item['size'],
                "inline": True
            },
            
            # LIGNE 2
            {
                "name": "🌟 Avis",
                "value": avis_display, # VRAIE INFO
                "inline": True
            },
            {
                "name": "💎 État",
                "value": item.get('condition', 'Très bon état'),
                "inline": True
            },
            {
                "name": "💰 Prix",
                "value": f"{prix} € | ≈ {prix_ttc} € (TTC)",
                "inline": True
            }
        ],
        
        "footer": {
            "text": f"Vinted Monster • Aujourd'hui à {datetime.now().strftime('%H:%M')}",
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
            await client.post(target_url, json=payload)
        except Exception as e:
            logger.error(f"❌ Erreur Discord : {e}")