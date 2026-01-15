import logging
import asyncio
import json
import os
from typing import List, Optional
from .browser import browser_manager

logger = logging.getLogger(__name__)

DB_FILE = "data/last_messages.json"

class KufarMessagingService:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.last_seen = self._load_db()

    def _load_db(self) -> dict:
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_db(self):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.last_seen, f, ensure_ascii=False, indent=2)

    async def _get_chat_details(self, page) -> Optional[dict]:
        # 1. Имя собеседника (сразу проверяем, не Куфар ли это)
        try:
            header_name_elem = page.locator("a[data-testid='mc-conversation-header-participant-link'] p span").first
            interlocutor_name = await header_name_elem.inner_text() if await header_name_elem.count() > 0 else "Собеседник"
        except:
            interlocutor_name = "Собеседник"

        # Игнорируем официальные уведомления Куфара
        if interlocutor_name == "Куфар":
            logger.info("⏩ Пропускаем системный чат Куфара")
            return None

        # 2. ID чата
        chat_id = "unknown"
        try:
            active_chat = page.locator("li.styles_menu-conversation-item_active__dNWHA div.styles_sides-block__QJXBM")
            if await active_chat.count() > 0:
                chat_id = await active_chat.get_attribute("data-conversation-id")
        except: pass

        # 3. История
        history_text = []
        last_msg_content = ""
        try:
            # Ищем пузыри, но игнорируем системные (mc-message-bubble-kufar)
            bubbles = await page.locator("[data-name='mc-message-bubble']").all()
            for bubble in bubbles:
                test_id = await bubble.get_attribute("data-testid")
                if test_id == "mc-message-bubble-kufar":
                    continue # Пропускаем "Оцените взаимодействие"
                
                text_elem = bubble.locator("p").first
                if await text_elem.count() > 0:
                    full_text = await text_elem.inner_text()
                    try:
                        time_span = text_elem.locator("span[class*='content_info']")
                        time_text = await time_span.inner_text() if await time_span.count() > 0 else ""
                        clean_text = full_text.replace(time_text, "").strip()
                    except:
                        clean_text = full_text.strip()
                    
                    last_msg_content = clean_text
                    name = "Вы" if test_id == "mc-message-bubble-receiver" else interlocutor_name
                    history_text.append(f"{name}: {clean_text}")

            if chat_id != "unknown" and self.last_seen.get(chat_id) == last_msg_content:
                return None

            if chat_id != "unknown":
                self.last_seen[chat_id] = last_msg_content
                self._save_db()

        except Exception as e:
            logger.error(f"Ошибка чтения истории: {e}")
            return None

        # 4. Товар
        try:
            ad_block = page.locator("a[data-testid='mc-conversation-header-ad']")
            product_name = await ad_block.locator("p").first.inner_text() if await ad_block.count() > 0 else "Товар"
            price = await ad_block.locator("p").nth(1).inner_text() if await ad_block.count() > 0 else "0"
        except:
            product_name, price = "Ошибка", "0"

        return {
            "id": chat_id,
            "product_name": product_name,
            "product_price": price,
            "history": "\n".join(history_text)
        }

    async def get_latest_chats(self, limit: int = 5) -> List[dict]:
        results = []
        async with browser_manager.get_page(use_session=True) as page:
            await page.set_viewport_size({"width": 1280, "height": 800})
            try:
                await page.goto("https://www.kufar.by/account/messaging/", wait_until="domcontentloaded")
                await page.wait_for_selector("li[data-testid='conversations-list-item']", timeout=15000)
                
                all_chats = await page.locator("li[data-testid='conversations-list-item']").all()
                for i, chat_elem in enumerate(all_chats[:limit]):
                    try:
                        await chat_elem.click()
                        await page.wait_for_timeout(1000)
                        details = await self._get_chat_details(page)
                        if details:
                            results.append(details)
                    except: continue
                return results
            except Exception as e:
                logger.error(f"Ошибка: {e}")
                return []

    async def send_message(self, chat_id: str, text: str) -> bool:
        async with browser_manager.get_page(use_session=True) as page:
            try:
                await page.goto("https://www.kufar.by/account/messaging/", wait_until="domcontentloaded")
                chat_selector = f"div[data-conversation-id='{chat_id}']"
                await page.wait_for_selector(chat_selector, timeout=10000)
                await page.locator(chat_selector).click()
                
                textarea = page.locator("textarea[name='message_textarea']")
                await textarea.wait_for(state="visible", timeout=5000)
                await textarea.fill(text)
                
                send_button = page.locator("button[type='submit'], label.styles_send-button__5c3Yw")
                await send_button.click()
                
                # --- ПРОВЕРКА ОТПРАВКИ ---
                await page.wait_for_timeout(1500) # Ждем реакции сайта
                current_value = await textarea.input_value()
                if current_value == "":
                    logger.info(f"✅ Сообщение в чат {chat_id} подтверждено")
                    return True
                else:
                    logger.warning(f"❌ Текст остался в поле чата {chat_id}")
                    return False
            except Exception as e:
                logger.error(f"Ошибка при отправке: {e}")
                return False
