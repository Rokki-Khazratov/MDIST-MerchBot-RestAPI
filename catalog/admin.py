"""
Catalog admin configuration.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum, Q
from django.urls import reverse
from catalog.models import Category, ImageAsset, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model."""
    
    list_display = ['name', 'slug', 'status_badge', 'sort_order', 'product_count', 'active_products_count']
    list_filter = ['is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order', 'name']
    list_editable = ['sort_order']
    
    actions = ['activate_categories', 'deactivate_categories']
    
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
        url = reverse('admin:catalog_product_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} products</a>', url, count)
    product_count.short_description = 'Total Products'
    
    def active_products_count(self, obj):
        """Display active products count."""
        count = obj.products.filter(is_active=True).count()
        return format_html('<strong style="color: green;">{}</strong>', count)
    active_products_count.short_description = 'Active'
    
    def activate_categories(self, request, queryset):
        """Bulk activate categories."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ {updated} category(ies) activated.')
    activate_categories.short_description = '✓ Activate selected categories'
    
    def deactivate_categories(self, request, queryset):
        """Bulk deactivate categories."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'⚠️ {updated} category(ies) deactivated.')
    deactivate_categories.short_description = '✗ Deactivate selected categories'


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
    fields = ['image_preview', 'image', 'sort_order', 'alt_text', 'is_primary']
    readonly_fields = ['image_preview']
    raw_id_fields = ['image']
    
    def image_preview(self, obj):
        """Display small image preview."""
        if obj.image and obj.image.file:
            return format_html(
                '<img src="{}" style="max-width: 80px; max-height: 80px; border-radius: 4px;" />',
                obj.image.file.url
            )
        return '-'
    image_preview.short_description = 'Preview'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for Product model."""
    
    list_display = [
        'thumbnail_display', 'name', 'category', 'price_display', 
        'stock_status', 'status_badge', 'is_new_badge', 'created_at'
    ]
    list_filter = [
        'is_active', 'category', 'created_at',
        ('discount_price', admin.EmptyFieldListFilter),
    ]
    search_fields = ['name', 'description', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = [
        'thumbnail_large', 'price_effective_display', 'discount_percentage',
        'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price', 'price_effective_display', 'discount_percentage'),
            'description': 'Set discount_price to create a sale price'
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
    
    actions = [
        'activate_products', 'deactivate_products', 
        'apply_10_discount', 'apply_20_discount', 'remove_discount'
    ]
    
    def thumbnail_display(self, obj):
        """Display small thumbnail in list."""
        primary_image = obj.get_primary_image()
        if primary_image and primary_image.file:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                primary_image.file.url
            )
        return format_html('<div style="width: 50px; height: 50px; background: #ddd; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px;">No image</div>')
    thumbnail_display.short_description = ''
    
    def thumbnail_large(self, obj):
        """Display large thumbnail in form."""
        primary_image = obj.get_primary_image()
        if primary_image and primary_image.file:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                primary_image.file.url
            )
        return 'No primary image set'
    thumbnail_large.short_description = 'Primary Image Preview'
    
    def price_display(self, obj):
        """Display price with discount indicator."""
        if obj.discount_price:
            discount_price_str = f"{float(obj.discount_price):,.2f}"
            price_str = f"{float(obj.price):,.2f}"
            return format_html(
                '<div style="font-weight: bold; color: #dc3545;">{} UZS</div>'
                '<div style="text-decoration: line-through; color: #6c757d; font-size: 0.85em;">{} UZS</div>',
                discount_price_str, price_str
            )
        price_str = f"{float(obj.price):,.2f}"
        return format_html('<div style="font-weight: bold;">{} UZS</div>', price_str)
    price_display.short_description = 'Price'
    
    def price_effective_display(self, obj):
        """Display effective price."""
        price = obj.price_effective
        if price is None:
            return '-'
        price_str = f"{float(price):,.2f}"
        return format_html('<strong>{} UZS</strong>', price_str)
    price_effective_display.short_description = 'Effective Price'
    
    def discount_percentage(self, obj):
        """Display discount percentage."""
        if obj.discount_price and obj.price > 0:
            percent = ((obj.price - obj.discount_price) / obj.price) * 100
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">-{}%</span>',
                int(percent)
            )
        return '-'
    discount_percentage.short_description = 'Discount'
    
    def stock_status(self, obj):
        """Display stock status with color."""
        if obj.quantity == 0:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px;">Out of stock</span>'
            )
        elif obj.quantity < 10:
            return format_html(
                '<span style="background: #ffc107; color: #000; padding: 3px 8px; border-radius: 3px;">{} left</span>',
                obj.quantity
            )
        return format_html(
            '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">{} in stock</span>',
            obj.quantity
        )
    stock_status.short_description = 'Stock'
    
    def status_badge(self, obj):
        """Display active status."""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">Hidden</span>'
        )
    status_badge.short_description = 'Status'
    
    def is_new_badge(self, obj):
        """Display 'New' badge for recent products."""
        from django.utils import timezone
        from datetime import timedelta
        from django.conf import settings
        
        is_new = obj.created_at >= timezone.now() - timedelta(days=settings.IS_NEW_PRODUCT_DAYS)
        if is_new:
            return format_html(
                '<span style="background: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">🆕 NEW</span>'
            )
        return ''
    is_new_badge.short_description = ''
    
    def activate_products(self, request, queryset):
        """Bulk activate products."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'✅ {updated} product(s) activated.')
    activate_products.short_description = '✓ Activate selected products'
    
    def deactivate_products(self, request, queryset):
        """Bulk deactivate products."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'⚠️ {updated} product(s) deactivated.')
    deactivate_products.short_description = '✗ Deactivate selected products'
    
    def apply_10_discount(self, request, queryset):
        """Apply 10% discount to selected products."""
        count = 0
        for product in queryset:
            product.discount_price = product.price * 0.9
            product.save()
            count += 1
        self.message_user(request, f'🎁 10% discount applied to {count} product(s).')
    apply_10_discount.short_description = '🎁 Apply 10%% discount'
    
    def apply_20_discount(self, request, queryset):
        """Apply 20% discount to selected products."""
        count = 0
        for product in queryset:
            product.discount_price = product.price * 0.8
            product.save()
            count += 1
        self.message_user(request, f'🎁 20% discount applied to {count} product(s).')
    apply_20_discount.short_description = '🎁 Apply 20%% discount'
    
    def remove_discount(self, request, queryset):
        """Remove discount from selected products."""
        updated = queryset.update(discount_price=None)
        self.message_user(request, f'💰 Discount removed from {updated} product(s).')
    remove_discount.short_description = '💰 Remove discount'
