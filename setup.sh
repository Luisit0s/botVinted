#!/bin/bash
echo "🔥 Initialisation du MONSTRE Vinted..."

# 1. Création environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 2. Installation dépendances
pip install -r requirements.txt

# 3. Installation navigateurs Playwright
playwright install chromium

# 4. Création fichier .env si inexistant
if [ ! -f .env ]; then
    echo "ENV=dev" > .env
    echo "DATABASE_URL=sqlite:///./bot_monster.db" >> .env
    echo "HEADLESS=False" >> .env
    echo "⚠️  Fichier .env créé. Pense à ajouter tes crédentials !"
fi

echo "✅ Installation terminée !"
echo "👉 Pour lancer : uvicorn app.main:app --reload"