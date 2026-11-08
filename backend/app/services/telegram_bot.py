from app.services.notifications import TelegramNotificationService

MENU = [
    ["Рассчитать заказ", "Магазины"],
    ["Доставка", "Как это работает"],
    ["Мои заявки", "Частые вопросы"],
    ["Связаться с менеджером", "Отправить ссылку на товар"],
]


class BuyerFlowBot:
    """Безопасный Telegram adapter: формирует меню и тексты, live polling включается отдельным worker."""

    def __init__(self, notifier=None):
        self.notifier = notifier or TelegramNotificationService()

    def menu(self):
        return {"keyboard": MENU, "resize_keyboard": True}

    def welcome(self):
        return "Добро пожаловать в BuyerFlow! Выберите действие в меню."

    def help_text(self):
        return "Отправьте ссылку на товар, цену, валюту и город доставки — мы подготовим предварительный расчёт."

    async def notify_new_order(self, number, product):
        return await self.notifier.notify_admin(f"Новая заявка {number}\n{product}")
