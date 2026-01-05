from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Identifiants (Optionnel)
    VINTED_USERNAME: str = ""
    VINTED_PASSWORD: str = ""
    
    # Base de données
    DATABASE_URL: str = "sqlite+aiosqlite:///./monster_vinted.db"
    
    # Configuration Robot
    # 🟢 IMPORTANT : True = Invisible / False = Visible
    HEADLESS: bool = True 
    
    # User Agent pour ne pas se faire repérer
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Ton Webhook Discord (Général)
    DISCORD_WEBHOOK_URL: str = "https://discord.com/api/webhooks/1446089152859738154/wF1GO-v9TrLWe18F4BdRAuB3U3OIwxLw2MPwrr2eQaKjwoBeY4cZaV8P7nDfnpSFDe-c"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()