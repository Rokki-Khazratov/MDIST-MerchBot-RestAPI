"""
Orders models: Order, OrderItem.
"""
from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings

from catalog.models import Product
from promos.models import PromoCode


class Order(models.Model):
    """Customer order with pricing snapshots."""
    
    # Payment method choices
    PAYMENT_CASH = 'cash'
    PAYMENT_CARD = 'card'
    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_CASH, 'Cash'),
        (PAYMENT_CARD, 'Card'),
    ]
    
    # Order status choices
    STATUS_NEW = 'new'
    STATUS_CONTACTED = 'contacted'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_CANCELED = 'canceled'
    STATUS_DELIVERED = 'delivered'
    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_CONTACTED, 'Contacted'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_CANCELED, 'Canceled'),
        (STATUS_DELIVERED, 'Delivered'),
    ]
    
    # Customer info
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=20,
        help_text='Phone number (no validation)'
    )
    telegram_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Telegram username WITH @ (e.g., @johndoe)'
    )
    
    # Payment
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        db_index=True
    )
    
    # Promo code (nullable)
    promo = models.ForeignKey(
        PromoCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    # Pricing (all in UZS)
    subtotal = models.DecimalField(
        max_digits=settings.DECIMAL_MAX_DIGITS,
        decimal_places=settings.DECIMAL_PLACES,
        help_text='Subtotal before discount'
    )
    discount_total = models.DecimalField(
        max_digits=settings.DECIMAL_MAX_DIGITS,
        decimal_places=settings.DECIMAL_PLACES,
        default=Decimal('0.00'),
        help_text='Total discount from promo code'
    )
    total = models.DecimalField(
        max_digits=settings.DECIMAL_MAX_DIGITS,
        decimal_places=settings.DECIMAL_PLACES,
        help_text='Final total (subtotal - discount_total)'
    )
    
    # Status and notes
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
        db_index=True
    )
    comment = models.TextField(
        blank=True,
        null=True,
        help_text='Customer comment'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Order #{self.pk} - {self.full_name} ({self.status})'
    
    def clean(self):
        """Validate order constraints."""
        if self.subtotal < 0:
            raise ValidationError('Subtotal must be non-negative')
        if self.discount_total < 0:
            raise ValidationError('Discount total must be non-negative')
        if self.total < 0:
            raise ValidationError('Total must be non-negative')
        
        # Validate total = subtotal - discount_total
        expected_total = self.subtotal - self.discount_total
        if self.total != expected_total:
            raise ValidationError(
                f'Total must equal subtotal - discount_total '
                f'(expected {expected_total}, got {self.total})'
            )


class OrderItem(models.Model):
    """
    Order line item with product snapshots.
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    
    # Snapshots at order time
    name_snapshot = models.CharField(
        max_length=255,
        help_text='Product name at order time'
    )
    price_snapshot = models.DecimalField(
        max_digits=settings.DECIMAL_MAX_DIGITS,
        decimal_places=settings.DECIMAL_PLACES,
        help_text='Effective price at order time (with discount if applicable)'
    )
    
    # Quantity and line total
    qty = models.IntegerField(help_text='Quantity ordered')
    line_total = models.DecimalField(
        max_digits=settings.DECIMAL_MAX_DIGITS,
        decimal_places=settings.DECIMAL_PLACES,
        help_text='Line total (price_snapshot * qty)'
    )
    
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        ordering = ['order', 'pk']
    
    def __str__(self):
        return f'{self.name_snapshot} x {self.qty}'
    
    def clean(self):
        """Validate order item constraints."""
        if self.qty <= 0:
            raise ValidationError('Quantity must be positive')
        if self.price_snapshot < 0:
            raise ValidationError('Price snapshot must be non-negative')
        if self.line_total < 0:
            raise ValidationError('Line total must be non-negative')
        
        # Validate line_total = price_snapshot * qty
        expected_line_total = self.price_snapshot * self.qty
        if self.line_total != expected_line_total:
            raise ValidationError(
                f'Line total must equal price_snapshot * qty '
                f'(expected {expected_line_total}, got {self.line_total})'
            )

