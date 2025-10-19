"""
Telegram Bot models.
"""
from django.db import models
from django.core.validators import RegexValidator
from orders.models import Order


class BotConfig(models.Model):
    """
    Telegram Bot configuration.
    
    Stores bot token, webhook URL, and notification group settings.
    Should be singleton - only one config per bot.
    """
    
    bot_token = models.CharField(
        max_length=200,
        help_text='Bot token from @BotFather'
    )
    
    webhook_url = models.URLField(
        blank=True,
        null=True,
        help_text='Webhook URL for receiving updates (e.g., https://your-domain.com/telegram/webhook/)'
    )
    
    notification_group_id = models.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex=r'^-?\d+$',
                message='Group ID must be a valid Telegram chat ID'
            )
        ],
        help_text='Telegram group ID where notifications will be sent (e.g., -1001234567890)'
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text='Enable/disable bot notifications'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Bot Configuration'
        verbose_name_plural = 'Bot Configuration'
    
    def __str__(self):
        return f'Bot Config (Active: {self.is_active})'
    
    def save(self, *args, **kwargs):
        """Ensure only one config exists (singleton pattern)."""
        if not self.pk and BotConfig.objects.exists():
            # Update existing config instead of creating new one
            existing = BotConfig.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)


class GroupNotification(models.Model):
    """
    History of notifications sent to Telegram group.
    
    Tracks all order notifications sent to managers group.
    """
    
    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_FAILED = 'failed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_FAILED, 'Failed'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='telegram_notifications'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    
    message_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Telegram message ID if sent successfully'
    )
    
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text='Error message if notification failed'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Group Notification'
        verbose_name_plural = 'Group Notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Notification for Order #{self.order.id} - {self.status}'
