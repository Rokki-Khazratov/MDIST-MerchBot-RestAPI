"""
Promo models: PromoCode.
"""
from decimal import Decimal

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class PromoCode(models.Model):
    """
    Promotional discount code with percentage-based discount.
    """
    
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Promo code (stored in UPPERCASE)'
    )
    percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text='Discount percentage (0.01 - 100.00)'
    )
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Optional date window for validity
    has_date_window = models.BooleanField(
        default=False,
        help_text='If True, promo is valid only between active_from and active_to'
    )
    active_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Start of validity period (timezone-aware)'
    )
    active_to = models.DateTimeField(
        null=True,
        blank=True,
        help_text='End of validity period (timezone-aware)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Promo Code'
        verbose_name_plural = 'Promo Codes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.code} (-{self.percent}%)'
    
    def clean(self):
        """Validate promo code constraints."""
        # Convert code to uppercase
        if self.code:
            self.code = self.code.upper()
        
        # Validate percent range
        if self.percent <= 0 or self.percent > 100:
            raise ValidationError('Percent must be between 0.01 and 100.00')
        
        # Validate date window
        if self.has_date_window:
            if not self.active_from or not self.active_to:
                raise ValidationError(
                    'Both active_from and active_to are required when has_date_window is True'
                )
            if self.active_from >= self.active_to:
                raise ValidationError('active_from must be before active_to')
    
    def save(self, *args, **kwargs):
        """Ensure code is uppercase before saving."""
        self.code = self.code.upper()
        self.full_clean()
        super().save(*args, **kwargs)
    
    def is_valid_now(self) -> bool:
        """
        Check if promo code is currently valid.
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not self.is_active:
            return False
        
        if self.has_date_window:
            now = timezone.now()
            if not (self.active_from <= now <= self.active_to):
                return False
        
        return True
    
    def get_validation_error(self) -> str | None:
        """
        Get error code if promo is invalid.
        
        Returns:
            str | None: Error code or None if valid
        """
        if not self.is_active:
            return 'PROMO_INACTIVE'
        
        if self.has_date_window:
            now = timezone.now()
            if not (self.active_from <= now <= self.active_to):
                return 'PROMO_EXPIRED'
        
        return None

