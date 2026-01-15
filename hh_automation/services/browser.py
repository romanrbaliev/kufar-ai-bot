import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from ..config import get_settings

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self) -> None:
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._lock = asyncio.Lock()
        self._settings = get_settings()

    async def start(self) -> None:
        async with self._lock:
            if self._playwright is None:
                logger.info("Starting Playwright...")
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=self._settings.browser_headless,
                    slow_mo=self._settings.browser_slow_mo
                )
                logger.info("Browser launched successfully")

    async def stop(self) -> None:
        async with self._lock:
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            logger.info("Browser stopped")

    @asynccontextmanager
    async def get_page(self, use_session: bool = True) -> AsyncGenerator[Page, None]:
        if not self._browser:
            await self.start()

        context: Optional[BrowserContext] = None
        try:
            if use_session and self._settings.session_file.exists():
                context = await self._browser.new_context(
                    storage_state=str(self._settings.session_file),
                    user_agent=self._settings.user_agent
                )
            else:
                context = await self._browser.new_context(
                    user_agent=self._settings.user_agent
                )

            page = await context.new_page()
            page.set_default_timeout(self._settings.page_timeout)
            yield page
        finally:
            if context:
                await context.close()

browser_manager = BrowserManager()
