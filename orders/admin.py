"""
Orders Django Admin configuration.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count
from django.urls import reverse
from orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Inline for OrderItem (readonly)."""
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ['product_link', 'name_snapshot', 'price_snapshot', 'qty', 'line_total_display']
    readonly_fields = ['product_link', 'name_snapshot', 'price_snapshot', 'qty', 'line_total_display']
    
    def product_link(self, obj):
        """Display link to product."""
        if obj.product:
            url = reverse('admin:catalog_product_change', args=[obj.product.id])
            return format_html('<a href="{}" target="_blank">View Product</a>', url)
        return '-'
    product_link.short_description = 'Product'
    
    def line_total_display(self, obj):
        """Display line total with formatting."""
        return format_html('<strong>{:,.2f} UZS</strong>', obj.line_total)
    line_total_display.short_description = 'Line Total'
    
    def has_add_permission(self, request, obj=None):
        """Disable adding order items in admin."""
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for Order."""
    list_display = (
        'order_id_display', 'customer_info', 'items_count', 'total_display',
        'status_badge', 'payment_badge', 'promo_badge', 'created_at'
    )
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('id', 'full_name', 'phone_number', 'telegram_username')
    readonly_fields = (
        'order_summary', 'subtotal_display', 'discount_total_display', 
        'total_display_large', 'created_at', 'updated_at'
    )
    inlines = [OrderItemInline]
    ordering = ['-created_at']
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Customer Information', {
            'fields': ('full_name', 'phone_number', 'telegram_username', 'comment'),
            'description': 'Customer contact details and order notes'
        }),
        ('Order Status', {
            'fields': ('status', 'payment_method'),
        }),
        ('Pricing & Promotion', {
            'fields': ('promo', 'subtotal_display', 'discount_total_display', 'total_display_large'),
        }),
        ('Order Summary', {
            'fields': ('order_summary',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_contacted', 'mark_confirmed', 'mark_completed', 'mark_cancelled',
        'export_to_csv'
    ]
    
    def order_id_display(self, obj):
        """Display order ID with formatting."""
        return format_html('<strong>#{}</strong>', obj.id)
    order_id_display.short_description = 'Order #'
    order_id_display.admin_order_field = 'id'
    
    def customer_info(self, obj):
        """Display customer name and contact."""
        telegram = f' (@{obj.telegram_username})' if obj.telegram_username else ''
        return format_html(
            '<div style="line-height: 1.4;"><strong>{}</strong><br/><small style="color: #666;">{}{}</small></div>',
            obj.full_name, obj.phone_number, telegram
        )
    customer_info.short_description = 'Customer'
    
    def items_count(self, obj):
        """Display number of items in order."""
        count = obj.items.count()
        total_qty = sum(item.qty for item in obj.items.all())
        return format_html(
            '<span style="background: #007bff; color: white; padding: 3px 8px; border-radius: 3px;">{} items ({} pcs)</span>',
            count, total_qty
        )
    items_count.short_description = 'Items'
    
    def total_display(self, obj):
        """Display total in list view."""
        html = f'<div style="text-align: right; line-height: 1.4;"><strong style="font-size: 14px;">{obj.total:,.2f} UZS</strong>'
        if obj.discount_total > 0:
            html += f'<br/><small style="color: #dc3545;">-{obj.discount_total:,.2f} UZS</small>'
        html += '</div>'
        return format_html(html)
    total_display.short_description = 'Total'
    total_display.admin_order_field = 'total'
    
    def subtotal_display(self, obj):
        """Display subtotal in detail view."""
        return format_html('<strong style="font-size: 16px;">{:,.2f} UZS</strong>', obj.subtotal)
    subtotal_display.short_description = 'Subtotal'
    
    def discount_total_display(self, obj):
        """Display discount in detail view."""
        if obj.discount_total > 0:
            return format_html(
                '<strong style="font-size: 16px; color: #dc3545;">-{:,.2f} UZS</strong>',
                obj.discount_total
            )
        return format_html('<span style="color: #6c757d;">No discount</span>')
    discount_total_display.short_description = 'Discount'
    
    def total_display_large(self, obj):
        """Display total with large formatting."""
        return format_html(
            '<div style="background: #28a745; color: white; padding: 15px; border-radius: 8px; text-align: center;">'
            '<div style="font-size: 12px; margin-bottom: 5px;">TOTAL AMOUNT</div>'
            '<div style="font-size: 28px; font-weight: bold;">{:,.2f} UZS</div>'
            '</div>',
            obj.total
        )
    total_display_large.short_description = 'Order Total'
    
    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            Order.STATUS_NEW: '#FFA500',  # Orange
            Order.STATUS_CONTACTED: '#1E90FF',  # Blue
            Order.STATUS_CONFIRMED: '#32CD32',  # Green
            Order.STATUS_COMPLETED: '#228B22',  # Dark Green
            Order.STATUS_CANCELLED: '#DC143C',  # Red
        }
        icons = {
            Order.STATUS_NEW: '🆕',
            Order.STATUS_CONTACTED: '📞',
            Order.STATUS_CONFIRMED: '✅',
            Order.STATUS_COMPLETED: '✔️',
            Order.STATUS_CANCELLED: '❌',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; border-radius: 4px; font-weight: bold;">{} {}</span>',
            colors.get(obj.status, '#666'),
            icons.get(obj.status, ''),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def payment_badge(self, obj):
        """Display payment method badge."""
        if obj.payment_method == 'cash':
            return format_html(
                '<span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 3px;">💵 Cash</span>'
            )
        return format_html(
            '<span style="background: #007bff; color: white; padding: 3px 8px; border-radius: 3px;">💳 Card</span>'
        )
    payment_badge.short_description = 'Payment'
    
    def promo_badge(self, obj):
        """Display promo code if used."""
        if obj.promo:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px;">🎁 {}</span>',
                obj.promo.code
            )
        return format_html('<span style="color: #6c757d;">-</span>')
    promo_badge.short_description = 'Promo'
    
    def order_summary(self, obj):
        """Display order summary card."""
        items_html = ''
        for item in obj.items.all():
            items_html += f'''
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{item.name_snapshot}</td>
                <td style="padding: 8px; border-bottom: 1px solid #dee2e6; text-align: center;">{item.qty}</td>
                <td style="padding: 8px; border-bottom: 1px solid #dee2e6; text-align: right;">{item.price_snapshot:,.2f} UZS</td>
                <td style="padding: 8px; border-bottom: 1px solid #dee2e6; text-align: right;"><strong>{item.line_total:,.2f} UZS</strong></td>
            </tr>
            '''
        
        promo_info = ''
        if obj.promo:
            promo_info = f'''
            <div style="background: #fff3cd; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                <strong>🎁 Promo Code Applied:</strong> {obj.promo.code} ({obj.promo.percent}% discount)
            </div>
            '''
        
        html = f'''
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            {promo_info}
            <h3 style="margin-top: 0;">📦 Order Items</h3>
            <table style="width: 100%; border-collapse: collapse; background: white;">
                <thead>
                    <tr style="background: #007bff; color: white;">
                        <th style="padding: 10px; text-align: left;">Product</th>
                        <th style="padding: 10px; text-align: center;">Qty</th>
                        <th style="padding: 10px; text-align: right;">Price</th>
                        <th style="padding: 10px; text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
                <tfoot>
                    <tr style="background: #e9ecef;">
                        <td colspan="3" style="padding: 10px; text-align: right;"><strong>Subtotal:</strong></td>
                        <td style="padding: 10px; text-align: right;"><strong>{obj.subtotal:,.2f} UZS</strong></td>
                    </tr>
                    <tr style="background: #e9ecef;">
                        <td colspan="3" style="padding: 10px; text-align: right;"><strong>Discount:</strong></td>
                        <td style="padding: 10px; text-align: right; color: #dc3545;"><strong>-{obj.discount_total:,.2f} UZS</strong></td>
                    </tr>
                    <tr style="background: #28a745; color: white;">
                        <td colspan="3" style="padding: 15px; text-align: right; font-size: 16px;"><strong>TOTAL:</strong></td>
                        <td style="padding: 15px; text-align: right; font-size: 18px;"><strong>{obj.total:,.2f} UZS</strong></td>
                    </tr>
                </tfoot>
            </table>
        </div>
        '''
        return format_html(html)
    order_summary.short_description = 'Detailed Summary'
    
    def mark_contacted(self, request, queryset):
        """Bulk action: mark as contacted."""
        updated = queryset.filter(status=Order.STATUS_NEW).update(status=Order.STATUS_CONTACTED)
        self.message_user(request, f'📞 {updated} order(s) marked as contacted')
    mark_contacted.short_description = '📞 Mark as Contacted'
    
    def mark_confirmed(self, request, queryset):
        """Bulk action: mark as confirmed."""
        updated = queryset.filter(status__in=[Order.STATUS_NEW, Order.STATUS_CONTACTED]).update(status=Order.STATUS_CONFIRMED)
        self.message_user(request, f'✅ {updated} order(s) marked as confirmed')
    mark_confirmed.short_description = '✅ Mark as Confirmed'
    
    def mark_completed(self, request, queryset):
        """Bulk action: mark as completed."""
        updated = queryset.update(status=Order.STATUS_COMPLETED)
        self.message_user(request, f'✔️ {updated} order(s) marked as completed')
    mark_completed.short_description = '✔️ Mark as Completed'
    
    def mark_cancelled(self, request, queryset):
        """Bulk action: mark as cancelled."""
        updated = queryset.update(status=Order.STATUS_CANCELLED)
        self.message_user(request, f'❌ {updated} order(s) marked as cancelled')
    mark_cancelled.short_description = '❌ Mark as Cancelled'
    
    def export_to_csv(self, request, queryset):
        """Export orders to CSV."""
        import csv
        from django.http import HttpResponse
        from django.utils import timezone
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="orders_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        response.write('\ufeff')  # UTF-8 BOM
        
        writer = csv.writer(response)
        writer.writerow(['Order ID', 'Customer', 'Phone', 'Telegram', 'Status', 'Payment', 'Promo', 'Subtotal', 'Discount', 'Total', 'Created'])
        
        for order in queryset:
            writer.writerow([
                order.id,
                order.full_name,
                order.phone_number,
                order.telegram_username or '',
                order.get_status_display(),
                order.payment_method,
                order.promo.code if order.promo else '',
                order.subtotal,
                order.discount_total,
                order.total,
                order.created_at.strftime('%Y-%m-%d %H:%M')
            ])
        
        self.message_user(request, f'📊 Exported {queryset.count()} order(s) to CSV')
        return response
    export_to_csv.short_description = '📊 Export to CSV'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Admin for OrderItem (for reference only)."""
    list_display = ('id', 'order_link', 'name_snapshot', 'price_snapshot', 'qty', 'line_total')
    list_filter = ('order__status', 'order__created_at')
    search_fields = ('name_snapshot', 'order__full_name')
    readonly_fields = ('order', 'product', 'name_snapshot', 'price_snapshot', 'qty', 'line_total')
    
    def order_link(self, obj):
        """Display link to order."""
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">Order #{}</a>', url, obj.order.id)
    order_link.short_description = 'Order'
    
    def has_add_permission(self, request):
        """Disable adding order items directly."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting order items."""
        return False
