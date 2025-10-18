"""
Promos Django Admin configuration.
"""
from django.contrib import admin
from promos.models import PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    """Admin for PromoCode."""
    list_display = ('code', 'percent', 'is_active', 'has_date_window', 'active_from', 'active_to', 'created_at')
    list_filter = ('is_active', 'has_date_window', 'created_at')
    search_fields = ('code',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('code', 'percent', 'is_active')
        }),
        ('Date Window (Optional)', {
            'fields': ('has_date_window', 'active_from', 'active_to'),
            'description': 'Enable date window to restrict promo code validity to specific period'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Convert code to uppercase before saving."""
        obj.code = obj.code.upper()
        super().save_model(request, obj, form, change)
