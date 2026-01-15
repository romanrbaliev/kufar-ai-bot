from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    # Настройки браузера
    browser_headless: bool = True
    browser_slow_mo: int = 50
    page_timeout: int = 30000 
    # Файл сессии теперь всегда лежит в папке data
    session_file: Path = Path("data/session.json")
    # Единый User-Agent для всего проекта
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Настройки мониторинга
    n8n_webhook_url: str = ""
    check_interval_min: int = 180
    check_interval_max: int = 300
    
    # Настройки сервера
    server_port: int = 8000
    server_host: str = "0.0.0.0"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

def get_settings():
    return Settings()
