"""
Telegram Bot views.
"""
import logging
import asyncio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from telegram_bot.services import TelegramService, WebhookService
from telegram_bot.exceptions import BotNotConfiguredError, BotInactiveError

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def webhook(request):
    """
    Telegram webhook endpoint.
    
    Receives updates from Telegram and processes them.
    
    POST /telegram/webhook/
    """
    try:
        # Get update data from request
        import json
        update_data = json.loads(request.body.decode('utf-8'))
        
        logger.info(f'Received webhook update: {update_data.get("update_id")}')
        
        # Process update asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            WebhookService.process_update(update_data)
        )
        loop.close()
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f'Webhook error: {e}')
        return JsonResponse(
            {'status': 'error', 'message': str(e)},
            status=500
        )


@api_view(['POST'])
def setup_webhook(request):
    """
    Setup webhook for Telegram bot.
    
    POST /telegram/setup-webhook/
    
    Request body:
    {
        "webhook_url": "https://your-domain.com/telegram/webhook/"
    }
    """
    try:
        webhook_url = request.data.get('webhook_url')
        
        if not webhook_url:
            return Response(
                {'error': 'webhook_url is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Setup webhook
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            TelegramService.set_webhook(webhook_url)
        )
        loop.close()
        
        if result:
            # Update config
            from telegram_bot.models import BotConfig
            config = BotConfig.objects.first()
            if config:
                config.webhook_url = webhook_url
                config.save()
            
            return Response({
                'status': 'success',
                'message': f'Webhook set to {webhook_url}',
                'webhook_url': webhook_url
            })
        else:
            return Response(
                {'error': 'Failed to set webhook'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except (BotNotConfiguredError, BotInactiveError) as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f'Setup webhook error: {e}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def webhook_info(request):
    """
    Get webhook information.
    
    GET /telegram/webhook-info/
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        info = loop.run_until_complete(
            TelegramService.get_webhook_info()
        )
        loop.close()
        
        return Response(info)
        
    except (BotNotConfiguredError, BotInactiveError) as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f'Get webhook info error: {e}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def delete_webhook(request):
    """
    Delete webhook.
    
    POST /telegram/delete-webhook/
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            TelegramService.delete_webhook()
        )
        loop.close()
        
        if result:
            # Update config
            from telegram_bot.models import BotConfig
            config = BotConfig.objects.first()
            if config:
                config.webhook_url = None
                config.save()
            
            return Response({
                'status': 'success',
                'message': 'Webhook deleted'
            })
        else:
            return Response(
                {'error': 'Failed to delete webhook'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    except (BotNotConfiguredError, BotInactiveError) as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f'Delete webhook error: {e}')
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
