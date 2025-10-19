"""
Telegram Bot signals.

Automatically send notifications when orders are created.
"""
import logging
import threading
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from orders.models import Order
from telegram_bot.services import NotificationService
from telegram_bot.exceptions import BotNotConfiguredError, BotInactiveError, NotificationFailedError

logger = logging.getLogger(__name__)


def _send_notification_async(order_id):
    """
    Send notification in a separate thread to avoid database locking.
    
    Args:
        order_id: Order ID to send notification for
    """
    try:
        # Get order from DB
        from orders.models import Order
        order = Order.objects.get(id=order_id)
        
        logger.info(f'Sending notification for order #{order_id}...')
        
        # Send notification
        notification = NotificationService.send_order_notification_sync(order)
        logger.info(f'Notification sent successfully: {notification.message_id}')
        
    except Order.DoesNotExist:
        logger.error(f'Order #{order_id} not found')
        
    except (BotNotConfiguredError, BotInactiveError) as e:
        # Bot is not configured or inactive - log and skip
        logger.warning(f'Bot not configured or inactive, skipping notification: {e}')
        
    except NotificationFailedError as e:
        # Notification failed - log error but don't raise
        logger.error(f'Failed to send notification for order #{order_id}: {e}')
        
    except Exception as e:
        # Unexpected error - log but don't raise
        logger.exception(f'Unexpected error sending notification for order #{order_id}: {e}')


@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    """
    Send notification to Telegram group when new order is created.
    
    Args:
        sender: Model class (Order)
        instance: Order instance
        created: True if order was created, False if updated
        **kwargs: Additional arguments
    """
    # Only send notification for newly created orders
    if not created:
        return
    
    logger.info(f'New order created: #{instance.id}, scheduling notification...')
    
    # Send notification after transaction commits to avoid database locking
    def send_after_commit():
        # Start notification in separate thread to avoid blocking
        thread = threading.Thread(target=_send_notification_async, args=(instance.id,))
        thread.daemon = True
        thread.start()
    
    transaction.on_commit(send_after_commit)

