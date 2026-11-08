import httpx
from app.core.config import settings


class NotificationService:
    async def notify_admin(self, text: str):
        raise NotImplementedError

    async def notify_client(self, chat_id: str, text: str):
        raise NotImplementedError


class MockNotificationService(NotificationService):
    def __init__(self):
        self.messages = []

    async def notify_admin(self, text):
        self.messages.append(("admin", text))

    async def notify_client(self, chat_id, text):
        self.messages.append((chat_id, text))


class TelegramNotificationService(NotificationService):
    async def _send(self, chat_id, text):
        if not settings.telegram_bot_token:
            return False
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage", json={"chat_id": chat_id, "text": text}
            )
            response.raise_for_status()
            return True

    async def notify_admin(self, text):
        return await self._send(settings.telegram_admin_chat_id, text) if settings.telegram_admin_chat_id else False

    async def notify_client(self, chat_id, text):
        return await self._send(chat_id, text)
