#!/usr/bin/env python3
"""
Run Telegram bot with polling for development.
"""
import asyncio
import os
import django
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'merchbot.settings')
django.setup()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram_bot.services.telegram import TelegramService
from telegram_bot.services.webhook import WebhookService
from asgiref.sync import sync_to_async

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context):
    """Handle /start command."""
    try:
        # Get bot config to check for Mini App URL
        config = await TelegramService.get_bot_config_async()
        
        if config and config.mini_app_url:
            # Create inline keyboard with Mini App button
            keyboard = [
                [InlineKeyboardButton("🛍️ Open Shop", url=config.mini_app_url)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "👋 Welcome to MDIST WEAR!\n"
                "The official merchandise project of MDIS Tashkent.\n\n"
                "Here you can browse, order, and represent your university with style.\n\n"
                "Please click the button below to open our shop👇",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "👋 Welcome to MDIST WEAR!\n"
                "The official merchandise project of MDIS Tashkent.\n\n"
                "Here you can browse, order, and represent your university with style.\n\n"
                "Mini App is currently being set up. Please check back later!"
            )
    except Exception as e:
        logger.error(f'Error in start command: {e}')
        await update.message.reply_text(
            "👋 Welcome to MDIST WEAR!\n"
            "The official merchandise project of MDIS Tashkent.\n\n"
            "Here you can browse, order, and represent your university with style."
        )

async def help_command(update: Update, context):
    """Handle /help command."""
    await update.message.reply_text(
        "📚 <b>Available Commands:</b>\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/status - Bot status\n"
        "/health - API health check",
        parse_mode='HTML'
    )

async def status_command(update: Update, context):
    """Handle /status command."""
    try:
        config = await TelegramService.get_bot_config_async()
        status_text = '✅ Active' if config.is_active else '❌ Inactive'
        
        response = f"🤖 <b>Bot Status</b>\n\n"
        response += f"Status: {status_text}\n"
        response += f"Group ID: {config.notification_group_id}\n"
        response += f"Webhook URL: {config.webhook_url or 'Not set'}\n"
        
        await update.message.reply_text(response, parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"❌ Error getting status: {e}")

async def health_command(update: Update, context):
    """Handle /health command."""
    try:
        import httpx
        from django.conf import settings
        
        async with httpx.AsyncClient() as client:
            api_response = await client.get(
                f'{settings.ADMIN_URL_PREFIX}/health/',
                timeout=5.0
            )
            
        if api_response.status_code == 200:
            await update.message.reply_text("✅ API is healthy and responding")
        else:
            await update.message.reply_text(f"⚠️ API returned status: {api_response.status_code}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ API health check failed: {e}")

async def handle_callback_query(update: Update, context):
    """Handle callback queries from inline buttons."""
    query = update.callback_query
    callback_data = query.data
    logger.info(f'Callback query received: {callback_data}')
    
    try:
        # Try to answer the callback query first (this might fail for old queries)
        try:
            await query.answer()
        except Exception as e:
            logger.warning(f'Could not answer callback query: {e}')
        
        if callback_data.startswith('order_success_'):
            # Handle successful order closure
            order_id = callback_data.replace('order_success_', '')
            await WebhookService._handle_order_success(query, order_id)
            
        elif callback_data.startswith('order_cancel_'):
            # Handle order cancellation
            order_id = callback_data.replace('order_cancel_', '')
            await WebhookService._handle_order_cancel(query, order_id)
            
        elif callback_data == 'test_success':
            await query.edit_message_text("✅ Test success button clicked!")
            
        elif callback_data == 'test_cancel':
            await query.edit_message_text("❌ Test cancel button clicked!")
            
        else:
            try:
                await query.answer("❓ Unknown command")
            except:
                pass
            
    except Exception as e:
        logger.error(f'Error handling callback query {callback_data}: {e}')
        try:
            await query.answer("❌ Error processing command")
        except:
            pass

def main():
    """Main function to run the bot."""
    try:
        # Get bot config
        config = TelegramService.get_bot_config()
        print(f"✅ Bot config found: {config.bot_token[:10]}...")
        print(f"✅ Mini App URL: {config.mini_app_url}")
        
        # Create application
        application = Application.builder().token(config.bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("health", health_command))
        application.add_handler(CallbackQueryHandler(handle_callback_query))
        
        print("🚀 Starting bot with polling...")
        print("📱 Bot will respond to /start command with Mini App button")
        print("Press Ctrl+C to stop")
        
        # Start polling
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
