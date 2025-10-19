"""
Catalog models: Category, Product, ProductImage.
"""
from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings


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
    
    def get_primary_image(self):
        """Get the primary image."""
        try:
            return self.productimage_set.filter(is_primary=True).first()
        except ProductImage.DoesNotExist:
            return None


class ProductImage(models.Model):
    """Product images with direct file upload."""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', help_text='Product image')
    sort_order = models.IntegerField(default=0, db_index=True)
    is_primary = models.BooleanField(
        default=False,
        help_text='Primary image (thumbnail) - exactly one per product'
    )
    
    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['product', 'sort_order']
    
    def __str__(self):
        return f'{self.product.name} - Image {self.sort_order}'
    
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
