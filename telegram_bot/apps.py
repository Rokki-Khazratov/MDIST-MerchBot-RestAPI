"""
Telegram Bot app configuration.
"""
from django.apps import AppConfig


class TelegramBotConfig(AppConfig):
    """Telegram Bot app config."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'telegram_bot'
    verbose_name = 'Telegram Bot'
    
    def ready(self):
        """Import signals when app is ready."""
        import telegram_bot.signals  # noqa: F401
