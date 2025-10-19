"""
Telegram Service - base class for Telegram API operations.
"""
import logging
from typing import Optional
from telegram import Bot
from telegram.error import TelegramError

from telegram_bot.models import BotConfig
from telegram_bot.exceptions import BotNotConfiguredError, BotInactiveError

logger = logging.getLogger(__name__)


class TelegramService:
    """
    Base service for Telegram Bot API operations.
    
    Provides methods for sending messages, setting up webhooks, etc.
    """
    
    @staticmethod
    def get_bot_config() -> BotConfig:
        """
        Get bot configuration.
        
        Returns:
            BotConfig: Bot configuration
            
        Raises:
            BotNotConfiguredError: If bot is not configured
            BotInactiveError: If bot is inactive
        """
        from asgiref.sync import async_to_sync
        
        # Check if we're in async context
        import asyncio
        try:
            asyncio.get_running_loop()
            # We're in async context - can't use sync DB calls
            # This shouldn't happen if we use sync_to_async properly
            logger.error('get_bot_config called from async context')
            raise BotNotConfiguredError()
        except RuntimeError:
            # We're in sync context - OK
            pass
        
        try:
            config = BotConfig.objects.first()
        except Exception as e:
            logger.error(f'Failed to get bot config: {e}')
            raise BotNotConfiguredError()
        
        if not config:
            raise BotNotConfiguredError()
        
        if not config.is_active:
            raise BotInactiveError()
        
        return config
    
    @staticmethod
    def get_bot() -> Bot:
        """
        Get Bot instance with configured token.
        
        Returns:
            Bot: Telegram Bot instance
            
        Raises:
            BotNotConfiguredError: If bot is not configured
            BotInactiveError: If bot is inactive
        """
        config = TelegramService.get_bot_config()
        return Bot(token=config.bot_token)
    
    @staticmethod
    async def send_message(
        chat_id: str,
        text: str,
        parse_mode: str = 'HTML',
        disable_web_page_preview: bool = False,
        reply_markup = None,
        bot_token: Optional[str] = None
    ) -> Optional[int]:
        """
        Send message to Telegram chat.
        
        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: Parse mode (HTML or Markdown)
            disable_web_page_preview: Disable link previews
            reply_markup: Inline keyboard markup
            bot_token: Bot token (if not provided, will get from config)
            
        Returns:
            int: Message ID if sent successfully, None otherwise
            
        Raises:
            NotificationFailedError: If message sending failed
        """
        if bot_token:
            bot = Bot(token=bot_token)
        else:
            bot = TelegramService.get_bot()
        
        try:
            message = await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                reply_markup=reply_markup
            )
            logger.info(f'Message sent to {chat_id}: {message.message_id}')
            return message.message_id
        except TelegramError as e:
            logger.error(f'Failed to send message to {chat_id}: {e}')
            raise
    
    @staticmethod
    async def set_webhook(webhook_url: str) -> bool:
        """
        Set webhook URL for bot.
        
        Args:
            webhook_url: Webhook URL
            
        Returns:
            bool: True if webhook was set successfully
            
        Raises:
            WebhookSetupError: If webhook setup failed
        """
        bot = TelegramService.get_bot()
        
        try:
            result = await bot.set_webhook(url=webhook_url)
            logger.info(f'Webhook set to {webhook_url}: {result}')
            return result
        except TelegramError as e:
            logger.error(f'Failed to set webhook: {e}')
            raise
    
    @staticmethod
    async def delete_webhook() -> bool:
        """
        Delete webhook.
        
        Returns:
            bool: True if webhook was deleted successfully
        """
        bot = TelegramService.get_bot()
        
        try:
            result = await bot.delete_webhook()
            logger.info(f'Webhook deleted: {result}')
            return result
        except TelegramError as e:
            logger.error(f'Failed to delete webhook: {e}')
            return False
    
    @staticmethod
    async def get_webhook_info() -> dict:
        """
        Get webhook information.
        
        Returns:
            dict: Webhook info
        """
        bot = TelegramService.get_bot()
        
        try:
            info = await bot.get_webhook_info()
            return {
                'url': info.url,
                'has_custom_certificate': info.has_custom_certificate,
                'pending_update_count': info.pending_update_count,
                'last_error_date': info.last_error_date,
                'last_error_message': info.last_error_message,
                'max_connections': info.max_connections,
                'allowed_updates': info.allowed_updates,
            }
        except TelegramError as e:
            logger.error(f'Failed to get webhook info: {e}')
            return {}

