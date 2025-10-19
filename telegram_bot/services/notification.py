"""
Notification Service - formatting and sending order notifications.
"""
import logging
from typing import Optional
from django.conf import settings
from telegram.error import TelegramError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from orders.models import Order
from telegram_bot.models import GroupNotification
from telegram_bot.services.telegram import TelegramService
from telegram_bot.exceptions import NotificationFailedError

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for formatting and sending order notifications to Telegram group.
    """
    
    @staticmethod
    def format_order_message(order: Order) -> str:
        """
        Format order as HTML message for Telegram.
        
        Args:
            order: Order instance
            
        Returns:
            str: Formatted HTML message
        """
        # Header
        message = f"🛒 <b>НОВЫЙ ЗАКАЗ #{order.id}</b>\n"
        message += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Customer info
        message += f"👤 <b>Клиент:</b> {order.full_name}\n"
        message += f"📞 <b>Телефон:</b> {order.phone_number}\n"
        
        if order.telegram_username:
            message += f"💬 <b>Telegram:</b> @{order.telegram_username}\n"
        
        message += "\n"
        
        # Order items
        message += "🛍️ <b>Товары:</b>\n"
        for item in order.items.all():
            product_name = item.name_snapshot
            qty = item.qty
            price_snapshot = item.price_snapshot
            total_item_price = price_snapshot * qty
            
            message += f"• {product_name} x{qty} - {float(total_item_price):,.0f} UZS\n"
        
        message += "\n━━━━━━━━━━━━━━━━━━━━\n"
        
        # Pricing
        message += f"💰 <b>Сумма:</b> {float(order.subtotal):,.0f} UZS\n"
        
        if order.promo:
            discount_amount = order.discount_total
            message += f"🎁 <b>Промокод:</b> {order.promo.code} (-{float(discount_amount):,.0f} UZS)\n"
        
        message += f"💳 <b>Итого:</b> <b>{float(order.total):,.0f} UZS</b>\n\n"
        
        # Additional info
        if order.comment:
            message += f"📝 <b>Комментарий:</b> {order.comment}\n"
        
        # Payment method
        payment_method_display = dict(Order.PAYMENT_METHOD_CHOICES).get(order.payment_method, order.payment_method)
        message += f"💳 <b>Оплата:</b> {payment_method_display}\n"
        
        # Order status
        status_display = dict(Order.STATUS_CHOICES).get(order.status, order.status)
        message += f"📦 <b>Статус:</b> {status_display}\n\n"
        
        # Admin link
        admin_url = f"{settings.ADMIN_URL_PREFIX or ''}/admin/orders/order/{order.id}/change/"
        message += f"🔗 <a href='{admin_url}'>Управление заказом</a>"
        
        return message
    
    @staticmethod
    async def send_order_notification(order: Order) -> GroupNotification:
        """
        Send order notification to managers group.
        
        Args:
            order: Order instance
            
        Returns:
            GroupNotification: Created notification record
            
        Raises:
            NotificationFailedError: If notification sending failed
        """
        from asgiref.sync import sync_to_async
        
        # Create notification record (sync)
        notification = await sync_to_async(GroupNotification.objects.create)(
            order=order,
            status=GroupNotification.STATUS_PENDING
        )
        
        try:
            # Get bot config (sync -> async)
            def _get_config():
                from telegram_bot.models import BotConfig
                config = BotConfig.objects.first()
                if not config:
                    from telegram_bot.exceptions import BotNotConfiguredError
                    raise BotNotConfiguredError()
                if not config.is_active:
                    from telegram_bot.exceptions import BotInactiveError
                    raise BotInactiveError()
                return config
            
            config = await sync_to_async(_get_config)()
            
            # Format message (sync -> async)
            message_text = await sync_to_async(NotificationService.format_order_message)(order)
            
            # Create inline keyboard with action buttons
            keyboard = [
                [
                    InlineKeyboardButton("✅ Закрыть как успешный", callback_data=f"order_success_{order.id}"),
                    InlineKeyboardButton("❌ Закрыть как отмена", callback_data=f"order_cancel_{order.id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send message with inline keyboard (async) - pass token directly to avoid sync DB calls in async
            message_id = await TelegramService.send_message(
                chat_id=config.notification_group_id,
                text=message_text,
                parse_mode='HTML',
                disable_web_page_preview=True,
                reply_markup=reply_markup,
                bot_token=config.bot_token
            )
            
            # Update notification record (sync)
            notification.status = GroupNotification.STATUS_SENT
            notification.message_id = str(message_id)
            await sync_to_async(notification.save)()
            
            logger.info(f'Order #{order.id} notification sent successfully: {message_id}')
            return notification
            
        except (TelegramError, Exception) as e:
            # Update notification record with error (sync)
            notification.status = GroupNotification.STATUS_FAILED
            notification.error_message = str(e)
            await sync_to_async(notification.save)()
            
            logger.error(f'Failed to send order #{order.id} notification: {e}')
            raise NotificationFailedError(str(e))
    
    @staticmethod
    def send_order_notification_sync(order: Order) -> GroupNotification:
        """
        Synchronous wrapper for send_order_notification.
        
        This method can be called from Django signals and views.
        
        Args:
            order: Order instance
            
        Returns:
            GroupNotification: Created notification record
        """
        import asyncio
        
        try:
            # Create new event loop if needed
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run async function in sync context
        return loop.run_until_complete(
            NotificationService.send_order_notification(order)
        )

