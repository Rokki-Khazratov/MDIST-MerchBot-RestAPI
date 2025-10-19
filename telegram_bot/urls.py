"""
Telegram Bot URL configuration.
"""
from django.urls import path
from telegram_bot import views

urlpatterns = [
    # Webhook endpoint
    path('webhook/', views.webhook, name='telegram-webhook'),
    
    # Webhook management
    path('setup-webhook/', views.setup_webhook, name='telegram-setup-webhook'),
    path('webhook-info/', views.webhook_info, name='telegram-webhook-info'),
    path('delete-webhook/', views.delete_webhook, name='telegram-delete-webhook'),
]


