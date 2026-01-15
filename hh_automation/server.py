import asyncio
import random
import logging
import aiohttp
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from hh_automation.services.kufar import KufarMessagingService
from hh_automation.config import get_settings

settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

kufar_service = KufarMessagingService()

async def send_to_n8n(data):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(settings.n8n_webhook_url, json=data) as response:
                if response.status == 200:
                    logger.info("🟢 n8n успешно принял данные (Код 200)")
                    return True
                else:
                    logger.error(f"🔴 n8n ОТКЛОНИЛ данные! Код: {response.status}. Проверьте, что Workflow ВКЛЮЧЕН (Active)")
                    return False
    except Exception as e:
        logger.error(f"❌ Ошибка связи с n8n: {e}")
        return False

async def monitor_kufar():
    logger.info("🤖 РОБОТ-МОНИТОР: Запускаюсь...")
    while True:
        try:
            logger.info("🔎 РОБОТ-МОНИТОР: Проверяю Куфар...")
            chats = await kufar_service.get_latest_chats(limit=5)
            if chats:
                logger.info(f"✅ РОБОТ-МОНИТОР: Нашел {len(chats)} чатов, отправляю в n8n")
                await send_to_n8n({"chats": chats})
            else:
                logger.info("😴 РОБОТ-МОНИТОР: Новых сообщений нет")
        except Exception as e:
            logger.error(f"🆘 РОБОТ-МОНИТОР: Ошибка в цикле мониторинга: {e}")

        wait_time = random.randint(settings.check_interval_min, settings.check_interval_max)
        logger.info(f"💤 РОБОТ-МОНИТОР: Сплю {wait_time} сек...")
        await asyncio.sleep(wait_time)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(monitor_kufar())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

class MessageRequest(BaseModel):
    chat_id: str
    text: str

@app.post("/send_message")
async def send_message(request: MessageRequest):
    logger.info(f"🦾 СИСТЕМА: Команда на отправку в {request.chat_id}")
    success = await kufar_service.send_message(request.chat_id, request.text)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=500, detail="Ошибка отправки")

if __name__ == "__main__":
    uvicorn.run(app, host=settings.server_host, port=settings.server_port)
