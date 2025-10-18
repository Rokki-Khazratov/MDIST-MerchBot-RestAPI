"""
Orders Django Admin configuration.
"""
from django.contrib import admin
from django.utils.html import format_html
from orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline for OrderItem (readonly)."""
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ['product', 'name_snapshot', 'price_snapshot', 'qty', 'line_total']
    readonly_fields = ['product', 'name_snapshot', 'price_snapshot', 'qty', 'line_total']
    
    def has_add_permission(self, request, obj=None):
        """Disable adding order items in admin."""
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for Order."""
    list_display = (
        'id', 'full_name', 'phone_number', 'status_badge',
        'total', 'payment_method', 'created_at'
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('full_name', 'phone_number', 'telegram_username')
    readonly_fields = (
        'subtotal', 'discount_total', 'total',
        'created_at', 'updated_at'
    )
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Customer Info', {
            'fields': ('full_name', 'phone_number', 'telegram_username')
        }),
        ('Order Details', {
            'fields': ('status', 'payment_method', 'promo', 'comment')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'discount_total', 'total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            Order.STATUS_NEW: '#FFA500',  # Orange
            Order.STATUS_CONTACTED: '#1E90FF',  # Blue
            Order.STATUS_CONFIRMED: '#32CD32',  # Green
            Order.STATUS_COMPLETED: '#228B22',  # Dark Green
            Order.STATUS_CANCELLED: '#DC143C',  # Red
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#666'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    actions = ['mark_contacted', 'mark_confirmed', 'mark_completed', 'mark_cancelled']
    
    def mark_contacted(self, request, queryset):
        """Bulk action: mark as contacted."""
        updated = queryset.update(status=Order.STATUS_CONTACTED)
        self.message_user(request, f'{updated} orders marked as contacted')
    mark_contacted.short_description = 'Mark as Contacted'
    
    def mark_confirmed(self, request, queryset):
        """Bulk action: mark as confirmed."""
        updated = queryset.update(status=Order.STATUS_CONFIRMED)
        self.message_user(request, f'{updated} orders marked as confirmed')
    mark_confirmed.short_description = 'Mark as Confirmed'
    
    def mark_completed(self, request, queryset):
        """Bulk action: mark as completed."""
        updated = queryset.update(status=Order.STATUS_COMPLETED)
        self.message_user(request, f'{updated} orders marked as completed')
    mark_completed.short_description = 'Mark as Completed'
    
    def mark_cancelled(self, request, queryset):
        """Bulk action: mark as cancelled."""
        updated = queryset.update(status=Order.STATUS_CANCELLED)
        self.message_user(request, f'{updated} orders marked as cancelled')
    mark_cancelled.short_description = 'Mark as Cancelled'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin for OrderItem (for reference only)."""
    list_display = ('id', 'order', 'name_snapshot', 'price_snapshot', 'qty', 'line_total')
    list_filter = ('order__status', 'order__created_at')
    search_fields = ('name_snapshot', 'order__full_name')
    readonly_fields = ('order', 'product', 'name_snapshot', 'price_snapshot', 'qty', 'line_total')
    
    def has_add_permission(self, request):
        """Disable adding order items directly."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting order items."""
        return False
