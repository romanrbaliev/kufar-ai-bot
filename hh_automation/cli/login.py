import asyncio
from playwright.async_api import async_playwright
from hh_automation.config import get_settings

async def main():
    settings = get_settings()
    print(f"🌍 Открываю Google Chrome для входа... (Сессия сохранится в: {settings.session_file})")

    async with async_playwright() as p:
        # channel="chrome" использует стабильную версию, которая не падает на Mac
        browser = await p.chromium.launch(headless=False, channel="chrome")
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto("https://www.kufar.by/login")

        print("\n" + "="*60)
        print("⚠️  ДЕЙСТВИЕ: Войди в аккаунт в открывшемся браузере.")
        print("   Как только увидишь свои сообщения - возвращайся сюда.")
        print("👉 Нажми ENTER в этом терминале, чтобы сохранить сессию.")
        print("="*60 + "\n")
        
        input()

        await context.storage_state(path=settings.session_file)
        print(f"✅ Успех! Сессия сохранена в {settings.session_file}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
