"""
Webhook Service - handling incoming Telegram updates.
"""
import logging
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import Application
from asgiref.sync import sync_to_async

from telegram_bot.services.telegram import TelegramService

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Service for handling incoming Telegram webhook updates.
    """
    
    @staticmethod
    async def process_update(update_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Process incoming webhook update from Telegram.
        
        Args:
            update_data: Update data from Telegram webhook
            
        Returns:
            dict: Processing result
        """
        try:
            # Get bot config (async)
            config = await TelegramService.get_bot_config_async()
            
            # Create application for update processing
            application = Application.builder().token(config.bot_token).build()
            
            # Create Update object from data
            update = Update.de_json(update_data, application.bot)
            
            if not update:
                logger.warning('Invalid update data received')
                return {'status': 'error', 'message': 'Invalid update data'}
            
            # Log update
            logger.info(f'Received update: {update.update_id}')
            
            # Process different update types
            if update.message:
                await WebhookService._handle_message(update)
            elif update.callback_query:
                await WebhookService._handle_callback_query(update)
            else:
                logger.info(f'Unhandled update type: {update}')
            
            return {'status': 'ok', 'message': 'Update processed'}
            
        except Exception as e:
            logger.error(f'Error processing update: {e}')
            return {'status': 'error', 'message': str(e)}
    
    @staticmethod
    async def _handle_message(update: Update) -> None:
        """
        Handle incoming message.
        
        Args:
            update: Telegram Update object
        """
        message = update.message
        
        if not message or not message.text:
            return
        
        text = message.text
        chat_id = message.chat_id
        
        logger.info(f'Message from {chat_id}: {text}')
        
        # Handle commands
        if text.startswith('/'):
            await WebhookService._handle_command(update, text)
        else:
            # Regular message - just log it
            logger.info(f'Regular message: {text}')
    
    @staticmethod
    async def _handle_command(update: Update, command: str) -> None:
        """
        Handle bot command.
        
        Args:
            update: Telegram Update object
            command: Command text
        """
        message = update.message
        
        if command == '/start':
            # Get bot config to check for Mini App URL
            def _get_config():
                from telegram_bot.models import BotConfig
                config = BotConfig.objects.first()
                return config
            
            config = await sync_to_async(_get_config)()
            
            if config and config.mini_app_url:
                # Create inline keyboard with Mini App button
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                keyboard = [
                    [InlineKeyboardButton("🛍️ Open Shop", url=config.mini_app_url)]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await message.reply_text(
                    '👋 Welcome to MDIST WEAR!\n'
                    'The official merchandise project of MDIS Tashkent.\n\n'
                    'Here you can browse, order, and represent your university with style.\n\n'
                    'Please click the button below to open our shop👇',
                    reply_markup=reply_markup
                )
            else:
                await message.reply_text(
                    '👋 Welcome to MDIST WEAR!\n'
                    'The official merchandise project of MDIS Tashkent.\n\n'
                    'Here you can browse, order, and represent your university with style.\n\n'
                    'Mini App is currently being set up. Please check back later!'
                )
        elif command == '/help':
            await message.reply_text(
                '📋 <b>Доступные команды:</b>\n\n'
                '/start - Начать\n'
                '/help - Помощь\n'
                '/status - Статус бота\n'
                '/health - Проверка связи с API',
                parse_mode='HTML'
            )
        elif command == '/status':
            # Get bot config (sync -> async)
            def _get_config():
                from telegram_bot.models import BotConfig
                config = BotConfig.objects.first()
                return config
            
            config = await sync_to_async(_get_config)()
            
            if not config:
                await message.reply_text('❌ Бот не настроен!')
                return
            
            status_text = '✅ Активен' if config.is_active else '❌ Неактивен'
            
            # Get webhook info
            webhook_info = await TelegramService.get_webhook_info()
            webhook_status = '✅ Настроен' if webhook_info.get('url') else '⚠️ Не настроен'
            
            response = (
                f'🤖 <b>СТАТУС БОТА</b>\n'
                f'━━━━━━━━━━━━━━━━\n\n'
                f'🔌 <b>Бот:</b> {status_text}\n'
                f'📡 <b>Webhook:</b> {webhook_status}\n'
                f'📢 <b>Группа ID:</b> <code>{config.notification_group_id}</code>\n\n'
            )
            
            if webhook_info.get('url'):
                response += f'🌐 <b>URL:</b> {webhook_info.get("url")}\n'
                response += f'📬 <b>Pending:</b> {webhook_info.get("pending_update_count", 0)}\n'
            
            await message.reply_text(response, parse_mode='HTML')
            
        elif command == '/health':
            import httpx
            from django.conf import settings
            
            # Check API health
            try:
                async with httpx.AsyncClient() as client:
                    api_response = await client.get(
                        f'{settings.ADMIN_URL_PREFIX}/health/',
                        timeout=5.0
                    )
                    
                    if api_response.status_code == 200:
                        api_status = '✅ OK'
                        api_details = api_response.json()
                    else:
                        api_status = f'❌ Error {api_response.status_code}'
                        api_details = {}
            except Exception as e:
                api_status = f'❌ Недоступен'
                api_details = {'error': str(e)}
            
            # Get bot config (sync -> async)
            def _get_config():
                from telegram_bot.models import BotConfig
                config = BotConfig.objects.first()
                if config:
                    return config.is_active
                return False
            
            bot_active = await sync_to_async(_get_config)()
            bot_status = '✅ Активен' if bot_active else '❌ Неактивен'
            
            # Get notification stats (sync -> async)
            def _get_stats():
                from telegram_bot.models import GroupNotification
                total = GroupNotification.objects.count()
                sent = GroupNotification.objects.filter(
                    status=GroupNotification.STATUS_SENT
                ).count()
                failed = GroupNotification.objects.filter(
                    status=GroupNotification.STATUS_FAILED
                ).count()
                return total, sent, failed
            
            total_notifications, sent_notifications, failed_notifications = await sync_to_async(_get_stats)()
            
            response_text = (
                f'🏥 <b>HEALTH CHECK</b>\n'
                f'━━━━━━━━━━━━━━━━\n\n'
                f'🤖 <b>Bot:</b> {bot_status}\n'
                f'🌐 <b>API:</b> {api_status}\n\n'
                f'📊 <b>Статистика уведомлений:</b>\n'
                f'  • Всего: {total_notifications}\n'
                f'  • Отправлено: {sent_notifications}\n'
                f'  • Ошибок: {failed_notifications}\n\n'
            )
            
            if api_details.get('timestamp'):
                response_text += f'⏰ API Time: {api_details.get("timestamp")}\n'
            
            await message.reply_text(response_text, parse_mode='HTML')
            
        else:
            await message.reply_text(
                '❓ Неизвестная команда. Используйте /help для списка команд.'
            )
    
    @staticmethod
    async def _handle_callback_query(update: Update) -> None:
        """
        Handle callback query from inline keyboard.
        
        Args:
            update: Telegram Update object
        """
        query = update.callback_query
        
        if not query:
            return
        
        callback_data = query.data
        logger.info(f'Callback query: {callback_data}')
        
        try:
            if callback_data.startswith('order_success_'):
                # Handle successful order closure
                order_id = callback_data.replace('order_success_', '')
                await WebhookService._handle_order_success(query, order_id)
                
            elif callback_data.startswith('order_cancel_'):
                # Handle order cancellation
                order_id = callback_data.replace('order_cancel_', '')
                await WebhookService._handle_order_cancel(query, order_id)
                
            else:
                await query.answer("❓ Неизвестная команда")
                
        except Exception as e:
            logger.error(f'Error handling callback query {callback_data}: {e}')
            await query.answer("❌ Произошла ошибка при обработке команды")
    
    @staticmethod
    async def _handle_order_success(query, order_id: str) -> None:
        """
        Handle successful order closure.
        """
        try:
            # Get order from DB (sync -> async)
            def _get_order():
                from orders.models import Order
                try:
                    return Order.objects.get(id=order_id)
                except Order.DoesNotExist:
                    return None
            
            order = await sync_to_async(_get_order)()
            
            if not order:
                await query.answer("❌ Заказ не найден")
                return
            
            # Update order status to confirmed (sync -> async)
            def _update_order():
                from orders.models import Order
                order.status = Order.STATUS_CONFIRMED
                order.save()
            
            await sync_to_async(_update_order)()
            
            # Update message text
            await query.edit_message_text(
                text=f"✅ <b>ЗАКАЗ #{order_id} УСПЕШНО ЗАКРЫТ</b>\n\n"
                     f"Статус: <b>Подтвержден</b>\n"
                     f"Клиент: {order.full_name}\n"
                     f"Сумма: {float(order.total):,.0f} UZS",
                parse_mode='HTML'
            )
            
            try:
                await query.answer("✅ Заказ успешно закрыт!")
            except:
                pass
            
        except Exception as e:
            logger.error(f'Error handling order success for #{order_id}: {e}')
            try:
                await query.answer("❌ Ошибка при закрытии заказа")
            except:
                pass
    
    @staticmethod
    async def _handle_order_cancel(query, order_id: str) -> None:
        """
        Handle order cancellation.
        """
        try:
            # Get order from DB (sync -> async)
            def _get_order():
                from orders.models import Order
                try:
                    return Order.objects.get(id=order_id)
                except Order.DoesNotExist:
                    return None
            
            order = await sync_to_async(_get_order)()
            
            if not order:
                await query.answer("❌ Заказ не найден")
                return
            
            # Store order info before deletion
            order_info = f"Заказ #{order_id}\nКлиент: {order.full_name}\nСумма: {float(order.total):,.0f} UZS"
            
            # Delete order completely from DB (sync -> async)
            def _delete_order():
                from orders.models import Order
                Order.objects.filter(id=order_id).delete()
            
            await sync_to_async(_delete_order)()
            
            # Update message text
            await query.edit_message_text(
                text=f"❌ <b>ЗАКАЗ ОТМЕНЕН И УДАЛЕН</b>\n\n"
                     f"{order_info}\n\n"
                     f"⚠️ Заказ полностью удален из базы данных",
                parse_mode='HTML'
            )
            
            await query.answer("❌ Заказ отменен и удален!")
            
        except Exception as e:
            logger.error(f'Error handling order cancellation for #{order_id}: {e}')
            await query.answer("❌ Ошибка при отмене заказа")

