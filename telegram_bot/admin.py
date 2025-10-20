"""
Telegram Bot admin configuration.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from telegram_bot.models import BotConfig, GroupNotification


@admin.register(BotConfig)
class BotConfigAdmin(admin.ModelAdmin):
    """Admin for Bot Configuration."""
    
    list_display = ['id', 'status_badge', 'notification_group_id', 'webhook_status', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Bot Credentials', {
            'fields': ('bot_token',)
        }),
        ('Notification Settings', {
            'fields': ('notification_group_id', 'is_active')
        }),
        ('Webhook Configuration', {
            'fields': ('webhook_url',),
            'description': 'Webhook URL for receiving Telegram updates'
        }),
        ('Mini App Configuration', {
            'fields': ('mini_app_url',),
            'description': 'Mini App URL for the shop (e.g., https://t.me/zzz/app)'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display bot status badge."""
        if obj.is_active:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">✗ Inactive</span>'
        )
    status_badge.short_description = 'Status'
    
    def webhook_status(self, obj):
        """Display webhook status."""
        if obj.webhook_url:
            return format_html(
                '<span style="background: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px;">✓ Configured</span>'
            )
        return format_html(
            '<span style="background: #ffc107; color: #000; padding: 3px 8px; border-radius: 3px;">⚠ Not Set</span>'
        )
    webhook_status.short_description = 'Webhook'
    
    def has_add_permission(self, request):
        """Only one config allowed (singleton)."""
        return not BotConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Don't allow deletion of config."""
        return False


@admin.register(GroupNotification)
class GroupNotificationAdmin(admin.ModelAdmin):
    """Admin for Group Notifications."""
    
    list_display = [
        'id', 'order_link', 'status_badge', 'message_id', 
        'created_at', 'error_display'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['order__id', 'order__full_name', 'message_id']
    readonly_fields = [
        'order', 'status', 'message_id', 'error_message', 
        'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    list_per_page = 50
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('order', 'status', 'message_id')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_link(self, obj):
        """Display link to order."""
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html(
            '<a href="{}">Order #{}</a>',
            url, obj.order.id
        )
    order_link.short_description = 'Order'
    
    def status_badge(self, obj):
        """Display status badge."""
        if obj.status == GroupNotification.STATUS_SENT:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✓ Sent</span>'
            )
        elif obj.status == GroupNotification.STATUS_FAILED:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✗ Failed</span>'
            )
        return format_html(
            '<span style="background: #ffc107; color: #000; padding: 3px 10px; border-radius: 3px; font-weight: bold;">⏳ Pending</span>'
        )
    status_badge.short_description = 'Status'
    
    def error_display(self, obj):
        """Display error message preview."""
        if obj.error_message:
            return format_html(
                '<span style="color: #dc3545; font-size: 0.9em;">{}</span>',
                obj.error_message[:50] + '...' if len(obj.error_message) > 50 else obj.error_message
            )
        return '-'
    error_display.short_description = 'Error'
    
    def has_add_permission(self, request):
        """Don't allow manual creation."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion for cleanup."""
        return True
