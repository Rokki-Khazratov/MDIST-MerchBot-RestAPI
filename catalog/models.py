"""
Catalog models: Category, ImageAsset, Product, ProductImage.
"""
import hashlib
from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from PIL import Image as PILImage


class Category(models.Model):
    """Product category (single level, no nesting)."""
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.IntegerField(default=0, db_index=True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class ImageAsset(models.Model):
    """
    Shared image asset pool with metadata and deduplication.
    """
    
    file = models.ImageField(upload_to='products/')
    width = models.IntegerField()
    height = models.IntegerField()
    content_type = models.CharField(max_length=50)
    sha256 = models.CharField(max_length=64, unique=True, db_index=True)
    file_size = models.IntegerField(help_text='File size in bytes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Image Asset'
        verbose_name_plural = 'Image Assets'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.file.name} ({self.width}x{self.height})'
    
    def clean(self):
        """Validate image format and size."""
        if not self.file:
            return
        
        # Check file size
        max_size = settings.IMAGE_MAX_SIZE_MB * 1024 * 1024
        if self.file.size > max_size:
            raise ValidationError(f'Image size exceeds {settings.IMAGE_MAX_SIZE_MB}MB limit')
        
        # Check format
        try:
            img = PILImage.open(self.file)
            format_lower = img.format.lower() if img.format else ''
            if format_lower not in settings.IMAGE_ALLOWED_FORMATS:
                raise ValidationError(
                    f'Invalid image format. Allowed: {", ".join(settings.IMAGE_ALLOWED_FORMATS)}'
                )
        except Exception as e:
            raise ValidationError(f'Invalid image file: {str(e)}')
    
    def save(self, *args, **kwargs):
        """Calculate metadata before saving."""
        if not self.pk and self.file:
            # Open image to get dimensions
            img = PILImage.open(self.file)
            self.width = img.width
            self.height = img.height
            self.content_type = f'image/{img.format.lower()}'
            self.file_size = self.file.size
            
            # Calculate SHA256 hash for deduplication
            self.file.seek(0)
            file_hash = hashlib.sha256()
            for chunk in self.file.chunks():
                file_hash.update(chunk)
            self.sha256 = file_hash.hexdigest()
            self.file.seek(0)
        
        super().save(*args, **kwargs)


class Product(models.Model):
    """Product with pricing and inventory."""
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(help_text='Full product description')
    
    price = models.DecimalField(
        max_digits=settings.DECIMAL_MAX_DIGITS,
        decimal_places=settings.DECIMAL_PLACES,
        help_text='Base price in UZS'
    )
    discount_price = models.DecimalField(
        max_digits=settings.DECIMAL_MAX_DIGITS,
        decimal_places=settings.DECIMAL_PLACES,
        null=True,
        blank=True,
        help_text='Discounted price in UZS (optional)'
    )
    
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    quantity = models.IntegerField(
        default=0,
        help_text='Stock quantity (indicator only, no auto-deduction)'
    )
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Images: M2M through ProductImage (no direct thumbnail FK)
    images = models.ManyToManyField(
        ImageAsset,
        through='ProductImage',
        related_name='products'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate pricing constraints."""
        if self.price < 0:
            raise ValidationError('Price must be non-negative')
        
        if self.discount_price is not None:
            if self.discount_price < 0:
                raise ValidationError('Discount price must be non-negative')
            if self.discount_price >= self.price:
                raise ValidationError('Discount price must be less than regular price')
        
        if self.quantity < 0:
            raise ValidationError('Quantity must be non-negative')
    
    @property
    def price_effective(self) -> Decimal:
        """Effective price (discount_price if set, otherwise price)."""
        return self.discount_price if self.discount_price else self.price
    
    def get_primary_image(self) -> 'ImageAsset':
        """Get the primary image (is_primary=True)."""
        try:
            return self.productimage_set.get(is_primary=True).image
        except ProductImage.DoesNotExist:
            return None


class ProductImage(models.Model):
    """
    Through table for Product <-> ImageAsset M2M relationship.
    Allows sorting, alt text, and primary image selection.
    """
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ForeignKey(ImageAsset, on_delete=models.PROTECT)
    sort_order = models.IntegerField(default=0, db_index=True)
    alt_text = models.CharField(max_length=255, blank=True, null=True)
    is_primary = models.BooleanField(
        default=False,
        help_text='Primary image (thumbnail) - exactly one per product'
    )
    
    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['product', 'sort_order']
        unique_together = [('product', 'image')]
    
    def __str__(self):
        return f'{self.product.name} - {self.image.file.name}'
    
    def clean(self):
        """Validate that exactly one image is primary per product."""
        if self.is_primary:
            # Check if another image is already primary for this product
            existing_primary = ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(pk=self.pk)
            
            if existing_primary.exists():
                raise ValidationError(
                    'This product already has a primary image. '
                    'Please unset the current primary image first.'
                )

