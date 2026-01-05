import asyncio
from playwright.async_api import async_playwright
from loguru import logger
from app.core.config import settings

class VintedAgent:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    async def start(self):
        """Démarre le navigateur."""
        if not self.playwright:
            logger.info("🚀 Démarrage de l'agent Playwright...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=settings.HEADLESS)
            self.page = await self.browser.new_page()
            await self.page.set_viewport_size({"width": 1280, "height": 720})

    async def search_items(self, keyword: str, max_price: float):
        """Lance une recherche et récupère les articles."""
        logger.info(f"🔎 Recherche : {keyword} (Max: {max_price}€)")

        if not self.page:
            await self.start()

        # 1. Navigation
        search_query = keyword.replace(" ", "+")
        url = f"https://www.vinted.fr/catalog?search_text={search_query}&price_to={max_price}&currency=EUR&order=newest_first"
        
        logger.info(f"🌍 Navigation vers : {url}")
        await self.page.goto(url)

        # 2. Gestion Cookies (Rapide)
        try:
            btn = self.page.get_by_role("button", name="Tout refuser")
            if await btn.is_visible():
                await btn.click()
                logger.info("🍪 Cookies refusés")
        except:
            pass

        # 3. Attente du chargement des articles
        # On attend que la grille d'articles apparaisse
        try:
            await self.page.wait_for_selector("div[data-testid='grid-item']", timeout=5000)
        except:
            logger.warning("⚠️ Aucun article trouvé ou chargement trop long")
            return []

        # 4. LE SCRAPING (La partie magique) 🪄
        logger.info("👀 Analyse des articles...")
        
        # On prend tous les articles de la page
        items_locators = await self.page.locator("div[data-testid='grid-item']").all()
        
        results = []
        # On regarde seulement les 5 premiers pour commencer (pour aller vite)
        for item in items_locators[:5]:
            try:
                # On essaie de trouver le lien dans l'article
                link_element = item.locator("a").first
                url_suffix = await link_element.get_attribute("href")
                full_url = url_suffix # Vinted met parfois l'url complète ou relative, on ajustera si besoin
                
                # On essaie de récupérer un titre (souvent dans l'attribut title du lien ou une image)
                title = await link_element.get_attribute("title")
                if not title:
                     # Plan B : Chercher une image avec un alt
                     img = item.locator("img").first
                     title = await img.get_attribute("alt")

                # On ajoute à notre liste de résultats
                results.append({
                    "title": title,
                    "url": full_url,
                    # "price": "À faire plus tard" (Le prix est plus dur à choper, on commence simple)
                })
            except Exception as e:
                # Si un article plante, on passe au suivant
                continue

        logger.info(f"✅ {len(results)} articles trouvés !")
        return results

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()