"""
Promos Django Admin configuration.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count
from promos.models import PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    """Admin for PromoCode."""
    list_display = (
        'code', 'discount_badge', 'status_badge', 'validity_status',
        'usage_count', 'created_at'
    )
    list_filter = ('is_active', 'has_date_window', 'created_at')
    search_fields = ('code',)
    readonly_fields = ('usage_stats', 'created_at', 'updated_at')
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('code', 'percent', 'is_active'),
            'description': 'Code will be automatically converted to UPPERCASE'
        }),
        ('Date Window (Optional)', {
            'fields': ('has_date_window', 'active_from', 'active_to'),
            'description': 'Enable date window to restrict promo code validity to specific period'
        }),
        ('Usage Statistics', {
            'fields': ('usage_stats',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_promos', 'deactivate_promos', 'extend_validity']
    
    def discount_badge(self, obj):
        """Display discount as colored badge."""
        if obj.percent >= 30:
            color = '#dc3545'  # Red for high discount
        elif obj.percent >= 15:
            color = '#ffc107'  # Yellow for medium
        else:
            color = '#28a745'  # Green for small
        
        return format_html(
            '<span style="background: {}; color: white; padding: 5px 12px; border-radius: 4px; font-weight: bold; font-size: 14px;">-{}%</span>',
            color, obj.percent
        )
    discount_badge.short_description = 'Discount'
    
    def status_badge(self, obj):
        """Display active status with badge."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✗ Inactive</span>'
        )
    status_badge.short_description = 'Status'
    
    def validity_status(self, obj):
        """Display validity status for date-restricted promos."""
        if not obj.has_date_window:
            return format_html(
                '<span style="color: #007bff; font-weight: bold;">∞ Unlimited</span>'
            )
        
        now = timezone.now()
        if now < obj.active_from:
            return format_html(
                '<span style="color: #ffc107;">⏰ Starts {}</span>',
                obj.active_from.strftime('%d.%m.%Y')
            )
        elif now > obj.active_to:
            return format_html(
                '<span style="color: #dc3545;">❌ Expired {}</span>',
                obj.active_to.strftime('%d.%m.%Y')
            )
        else:
            return format_html(
                '<span style="color: #28a745;">✓ Valid until {}</span>',
                obj.active_to.strftime('%d.%m.%Y')
            )
    validity_status.short_description = 'Validity'
    
    def usage_count(self, obj):
        """Display how many times promo was used."""
        count = obj.orders.count()
        if count == 0:
            return format_html('<span style="color: #6c757d;">Not used yet</span>')
        elif count < 5:
            return format_html('<span style="color: #28a745; font-weight: bold;">{} times</span>', count)
        else:
            return format_html('<span style="color: #dc3545; font-weight: bold;">🔥 {} times</span>', count)
    usage_count.short_description = 'Usage'
    
    def usage_stats(self, obj):
        """Display detailed usage statistics."""
        orders = obj.orders.all()
        count = orders.count()
        
        if count == 0:
            return 'This promo code has not been used yet.'
        
        total_discount = sum(o.discount_total for o in orders)
        total_revenue = sum(o.total for o in orders)
        
        html = f'''
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
            <h3 style="margin-top: 0;">📊 Usage Statistics</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Total Usage:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{count} orders</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Total Discount Given:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #dc3545; font-weight: bold;">{total_discount:,.2f} UZS</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6;"><strong>Total Revenue:</strong></td>
                    <td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: #28a745; font-weight: bold;">{total_revenue:,.2f} UZS</td>
                </tr>
                <tr>
                    <td style="padding: 8px;"><strong>Average Order:</strong></td>
                    <td style="padding: 8px;">{total_revenue / count:,.2f} UZS</td>
                </tr>
            </table>
        </div>
        '''
        return format_html(html)
    usage_stats.short_description = 'Detailed Statistics'
    
    def activate_promos(self, request, queryset):
        """Bulk activate promo codes."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ {updated} promo code(s) activated.')
    activate_promos.short_description = '✓ Activate selected promos'
    
    def deactivate_promos(self, request, queryset):
        """Bulk deactivate promo codes."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'⚠️ {updated} promo code(s) deactivated.')
    deactivate_promos.short_description = '✗ Deactivate selected promos'
    
    def extend_validity(self, request, queryset):
        """Extend validity by 30 days for date-restricted promos."""
        from datetime import timedelta
        updated = 0
        for promo in queryset.filter(has_date_window=True):
            promo.active_to = promo.active_to + timedelta(days=30)
            promo.save()
            updated += 1
        self.message_user(request, f'📅 Extended validity by 30 days for {updated} promo(s).')
    extend_validity.short_description = '📅 Extend validity by 30 days'
    
    def save_model(self, request, obj, form, change):
        """Convert code to uppercase before saving."""
        obj.code = obj.code.upper()
        super().save_model(request, obj, form, change)
