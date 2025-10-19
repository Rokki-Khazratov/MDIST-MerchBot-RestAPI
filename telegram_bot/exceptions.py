"""
Telegram Bot custom exceptions.
"""


class TelegramBotError(Exception):
    """Base exception for Telegram Bot errors."""
    pass


class BotNotConfiguredError(TelegramBotError):
    """Bot is not configured."""
    def __init__(self):
        super().__init__('Telegram bot is not configured. Please configure bot in admin panel.')


class BotInactiveError(TelegramBotError):
    """Bot is inactive."""
    def __init__(self):
        super().__init__('Telegram bot is inactive. Please enable bot in admin panel.')


class NotificationFailedError(TelegramBotError):
    """Notification failed to send."""
    def __init__(self, message: str):
        super().__init__(f'Failed to send notification: {message}')


class WebhookSetupError(TelegramBotError):
    """Webhook setup failed."""
    def __init__(self, message: str):
        super().__init__(f'Failed to setup webhook: {message}')


