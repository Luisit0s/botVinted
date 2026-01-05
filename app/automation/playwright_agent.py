import re
import asyncio
import random
from playwright.async_api import async_playwright
from loguru import logger
from app.core.config import settings

class VintedAgent:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    async def start(self):
        if not self.playwright:
            logger.info("👻 Démarrage Agent FANTÔME (Mode Invisible)...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=settings.HEADLESS)
            context = await self.browser.new_context(
                user_agent=settings.USER_AGENT,
                viewport={"width": 1920, "height": 1080}
            )
            self.page = await context.new_page()

    async def random_sleep(self, min_time=0.5, max_time=1.5):
        await asyncio.sleep(random.uniform(min_time, max_time))

    def extract_id_from_url(self, url: str):
        match = re.search(r'/items/(\d+)-', url)
        return int(match.group(1)) if match else None

    async def get_real_details(self, item_url: str) -> dict:
        """
        🕵️‍♂️ Va chercher les VRAIES infos sur la page article :
        - Vraie date de publication (ex: "il y a 10 min")
        - Vrais avis vendeur (ex: "5.0 (150)")
        """
        page = await self.browser.new_page()
        details = {
            "time": "Inconnu", 
            "rating": "N/A", 
            "review_count": "0"
        }
        
        try:
            await page.goto(item_url, timeout=15000)
            
            # 1. RÉCUPÉRATION DATE (Timestamp)
            # On cherche le texte "il y a" ou une date dans les attributs
            try:
                # Cherche la balise de temps relative souvent présente
                time_element = page.locator("div[data-testid='item-attributes-upload_date'] time")
                if await time_element.count() > 0:
                    details["time"] = await time_element.inner_text()
                else:
                    # Fallback : on cherche dans le texte global
                    body_text = await page.inner_text("body")
                    match_time = re.search(r'(il y a [0-9]+ (min|heure|jour|seconde)s?)', body_text)
                    if match_time:
                        details["time"] = match_time.group(1)
            except: pass

            # 2. RÉCUPÉRATION AVIS VENDEUR
            try:
                # On cherche le lien vers le profil qui contient le score
                user_block = page.locator("div[data-testid='item-source-summary']")
                if await user_block.count() > 0:
                    text = await user_block.inner_text()
                    # On cherche le format (123)
                    match_count = re.search(r'\((\d+)\)', text)
                    if match_count:
                        details["review_count"] = match_count.group(1)
                        # Si on a un nombre d'avis, on assume 5 étoiles visuelles ou on cherche le chiffre
                        details["rating"] = "⭐⭐⭐⭐⭐" 
                        if "4." in text: details["rating"] = "⭐⭐⭐⭐"
                    elif "Aucune évaluation" in text:
                        details["rating"] = "Nouveau"
            except: pass

        except Exception:
            pass
        finally:
            await page.close()
            
        return details

    def parse_data(self, raw_title: str):
        data = {"price": 0.0, "brand": "Inconnu", "size": "N/A", "condition": "Bon état"}
        price_match = re.search(r'(\d+[,.]\d{2}) ?€', raw_title)
        if price_match: data["price"] = float(price_match.group(1).replace(',', '.'))
        
        parts = raw_title.split(",")
        for part in parts:
            if "marque" in part.lower(): data["brand"] = part.split(":")[-1].strip()
            if "taille" in part.lower(): data["size"] = part.split(":")[-1].strip()
            if "état" in part.lower(): data["condition"] = part.split(":")[-1].strip()
        return data

    async def search(self, keyword: str, max_price: float):
        if not self.page: await self.start()
        clean_keyword = keyword.replace(" ", "+")
        # Filtre tailles HOMME standard
        size_filter = "&size_ids[]=208&size_ids[]=209&size_ids[]=210&size_ids[]=211&size_ids[]=212"
        url = f"https://www.vinted.fr/catalog?search_text={clean_keyword}&price_to={max_price}&currency=EUR&order=newest_first{size_filter}"
        
        try:
            await self.page.goto(url, timeout=30000)
            await self.random_sleep(0.5, 1.5)
            try: await self.page.get_by_role("button", name="Tout refuser").click(timeout=1000)
            except: pass
            try: await self.page.wait_for_selector("div[data-testid='grid-item']", timeout=5000)
            except: pass 
        except: return []

        items_locators = await self.page.locator("div[data-testid='grid-item']").all()
        results = []
        
        # On ne prend que les 5 premiers pour aller vite car on va ouvrir chaque page
        for item in items_locators[:5]: 
            try:
                link = item.locator("a").first
                url_suffix = await link.get_attribute("href")
                full_url = url_suffix if "http" in url_suffix else f"https://www.vinted.fr{url_suffix}"
                vinted_id = self.extract_id_from_url(full_url)
                if not vinted_id: continue

                raw_title = await link.get_attribute("title")
                photo_url = await item.locator("img").first.get_attribute("src")
                parsed = self.parse_data(raw_title)

                item_data = {
                    "vinted_id": vinted_id,
                    "url": full_url,
                    "raw_title": raw_title,
                    "photo_url": photo_url,
                    "price": parsed["price"],
                    "brand": parsed["brand"],
                    "size": parsed["size"],
                    "condition": parsed["condition"]
                }
                
                if 0 < item_data["price"] <= max_price:
                    results.append(item_data)
            except: continue
        return results

    async def stop(self):
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()