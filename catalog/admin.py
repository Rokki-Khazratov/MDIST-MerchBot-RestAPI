"""
Catalog admin configuration.
"""
from django.contrib import admin
from django.utils.html import format_html
from catalog.models import Category, ImageAsset, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model."""
    
    list_display = ['name', 'slug', 'is_active', 'sort_order', 'product_count']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order', 'name']
    
    def product_count(self, obj):
        """Display number of products in category."""
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(ImageAsset)
class ImageAssetAdmin(admin.ModelAdmin):
    """Admin for ImageAsset model."""
    
    list_display = ['id', 'image_preview', 'file_name', 'dimensions', 'file_size_display', 'created_at']
    list_filter = ['created_at']
    search_fields = ['file', 'sha256']
    readonly_fields = ['image_preview', 'width', 'height', 'content_type', 'sha256', 'file_size', 'created_at']
    ordering = ['-created_at']
    
    def image_preview(self, obj):
        """Display image preview."""
        if obj.file:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.file.url
            )
        return '-'
    image_preview.short_description = 'Preview'
    
    def file_name(self, obj):
        """Display file name."""
        return obj.file.name if obj.file else '-'
    file_name.short_description = 'File'
    
    def dimensions(self, obj):
        """Display image dimensions."""
        return f'{obj.width}x{obj.height}'
    dimensions.short_description = 'Size'
    
    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        size = obj.file_size
        if size < 1024:
            return f'{size} B'
        elif size < 1024 * 1024:
            return f'{size / 1024:.1f} KB'
        else:
            return f'{size / (1024 * 1024):.1f} MB'
    file_size_display.short_description = 'File Size'


class ProductImageInline(admin.TabularInline):
    """Inline for ProductImage through model."""
    
    model = ProductImage
    extra = 1
    fields = ['image', 'sort_order', 'alt_text', 'is_primary']
    raw_id_fields = ['image']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for Product model."""
    
    list_display = [
        'name', 'category', 'price', 'discount_price', 'price_effective_display',
        'quantity', 'is_active', 'created_at'
    ]
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['name', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['price_effective_display', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
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
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProductImageInline]
    
    def price_effective_display(self, obj):
        """Display effective price."""
        return f'{obj.price_effective:.2f} UZS'
    price_effective_display.short_description = 'Effective Price'
    
    actions = ['activate_products', 'deactivate_products']
    
    def activate_products(self, request, queryset):
        """Bulk activate products."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} product(s) activated.')
    activate_products.short_description = 'Activate selected products'
    
    def deactivate_products(self, request, queryset):
        """Bulk deactivate products."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} product(s) deactivated.')
    deactivate_products.short_description = 'Deactivate selected products'
