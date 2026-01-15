import asyncio
from playwright.async_api import async_playwright
from hh_automation.config import get_settings
import os

async def main():
    settings = get_settings()
    # Создаем папку data, если её нет
    os.makedirs("data", exist_ok=True)
    
    print(f"🌍 Открываю браузер... (Сессия сохранится в: {settings.session_file})")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        # Важно использовать тот же User-Agent, что и в боте
        context = await browser.new_context(user_agent=settings.user_agent)
        page = await context.new_page()

        await page.goto("https://www.kufar.by/login")

        print("\n" + "="*60)
        print("⚠️  ДЕЙСТВИЕ: Войди в аккаунт.")
        print("👉 После входа нажми ENTER в терминале.")
        print("="*60 + "\n")
        
        input()

        await context.storage_state(path=str(settings.session_file))
        print(f"✅ Успех! Файл создан: {settings.session_file}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
