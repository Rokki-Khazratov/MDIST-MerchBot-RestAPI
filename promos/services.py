"""
Promos business logic (validation, discount calculation).
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple, Optional
from django.utils import timezone

from promos.models import PromoCode
from merchbot.exceptions import PromoNotFoundError, PromoInactiveError, PromoExpiredError


class PromoService:
    """Service for promo code validation and discount calculation."""
    
    @staticmethod
    def validate_promo(code: str) -> PromoCode:
        """
        Validate promo code and return it if valid.
        
        Args:
            code: Promo code (case-insensitive)
            
        Returns:
            PromoCode: Valid promo code object
            
        Raises:
            PromoNotFoundError: Promo code not found
            PromoInactiveError: Promo code is not active
            PromoExpiredError: Promo code has expired
        """
        # Find promo code (case-insensitive)
        promo = PromoCode.objects.filter(code__iexact=code).first()
        
        if not promo:
            raise PromoNotFoundError()
        
        if not promo.is_active:
            raise PromoInactiveError()
        
        # Check date window if applicable
        if promo.has_date_window:
            now = timezone.now()
            if not (promo.active_from <= now <= promo.active_to):
                raise PromoExpiredError()
        
        return promo
    
    @staticmethod
    def calculate_discount(subtotal: Decimal, promo: PromoCode) -> Tuple[Decimal, Decimal]:
        """
        Calculate discount amount and final total.
        
        Args:
            subtotal: Subtotal before discount
            promo: Promo code object
            
        Returns:
            Tuple[Decimal, Decimal]: (discount_total, total)
        """
        # Calculate discount with proper rounding
        discount_total = (subtotal * promo.percent / Decimal('100')).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
        
        total = subtotal - discount_total
        
        return discount_total, total
    
    @staticmethod
    def validate_and_calculate(
        code: str,
        subtotal: Decimal
    ) -> Tuple[PromoCode, Decimal, Decimal]:
        """
        Validate promo code and calculate discount in one call.
        
        Args:
            code: Promo code
            subtotal: Subtotal before discount
            
        Returns:
            Tuple[PromoCode, Decimal, Decimal]: (promo, discount_total, total)
            
        Raises:
            PromoNotFoundError, PromoInactiveError, PromoExpiredError
        """
        promo = PromoService.validate_promo(code)
        discount_total, total = PromoService.calculate_discount(subtotal, promo)
        return promo, discount_total, total
