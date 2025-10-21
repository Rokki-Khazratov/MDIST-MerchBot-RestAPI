"""
Catalog admin configuration.
"""
from django.contrib import admin
from django.utils.html import format_html
from catalog.models import Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model."""
    
    list_display = ['name', 'slug', 'status_badge', 'sort_order', 'product_count']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order', 'name']
    list_editable = ['sort_order']
    
    def status_badge(self, obj):
        """Display status with color badge."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✗ Inactive</span>'
        )
    status_badge.short_description = 'Status'
    
    def product_count(self, obj):
        """Display total number of products in category."""
        count = obj.products.count()
        return format_html('<strong>{}</strong> products', count)
    product_count.short_description = 'Products'


class ProductImageInline(admin.TabularInline):
    """Inline for ProductImage - simple and clean."""
    
    model = ProductImage
    extra = 1
    fields = ['image', 'sort_order']
    can_delete = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for Product model."""
    
    list_display = [
        'thumbnail_display', 'name', 'category', 'price_display', 
        'stock_status', 'status_badge', 'created_at'
    ]
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['name', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['thumbnail_large', 'price_effective_display', 'created_at', 'updated_at']
    ordering = ['-created_at']
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price', 'price_effective_display')
        }),
        ('Inventory', {
            'fields': ('quantity', 'is_active')
        }),
        ('Preview', {
            'fields': ('thumbnail_large',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProductImageInline]
    
    def save_formset(self, request, form, formset, change):
        """Handle inline formset saving."""
        instances = formset.save(commit=False)
        
        # Only save instances that have an image
        for instance in instances:
            if instance.image:  # Only save if image is provided
                instance.save()
        
        # Delete marked for deletion
        for instance in formset.deleted_objects:
            instance.delete()
    
    def thumbnail_display(self, obj):
        """Display small thumbnail in list."""
        primary_image = obj.get_primary_image()
        if primary_image and primary_image.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                primary_image.image.url
            )
        return format_html('<div style="width: 50px; height: 50px; background: #ddd; border-radius: 4px;"></div>')
    thumbnail_display.short_description = ''
    
    def thumbnail_large(self, obj):
        """Display large thumbnail in form."""
        primary_image = obj.get_primary_image()
        if primary_image and primary_image.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; border-radius: 8px;" />',
                primary_image.image.url
            )
        return 'No images uploaded'
    thumbnail_large.short_description = 'Primary Image'
    
    def price_display(self, obj):
        """Display price with discount indicator."""
        if obj.discount_price:
            return format_html(
                '<div style="font-weight: bold; color: #dc3545;">{} сум</div>'
                '<div style="text-decoration: line-through; color: #999; font-size: 0.85em;">{} сум</div>',
                f"{float(obj.discount_price):,.0f}", f"{float(obj.price):,.0f}"
            )
        return format_html('<div style="font-weight: bold;">{} сум</div>', f"{float(obj.price):,.0f}")
    price_display.short_description = 'Price'
    
    def price_effective_display(self, obj):
        """Display effective price."""
        if obj.price_effective is None:
            return format_html('<strong>Не указана</strong>')
        return format_html('<strong>{} сум</strong>', f"{float(obj.price_effective):,.0f}")
    price_effective_display.short_description = 'Effective Price'
    
    def stock_status(self, obj):
        """Display stock status with color."""
        if obj.quantity == 0:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px;">Out</span>'
            )
        elif obj.quantity < 10:
            return format_html(
                '<span style="background: #ffc107; color: #000; padding: 3px 8px; border-radius: 3px;">{}</span>',
                obj.quantity
            )
        return format_html(
            '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            obj.quantity
        )
    stock_status.short_description = 'Stock'
    
    def status_badge(self, obj):
        """Display active status."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px;">✗</span>'
        )
    status_badge.short_description = 'Active'
