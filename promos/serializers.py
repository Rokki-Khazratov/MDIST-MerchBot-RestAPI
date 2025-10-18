"""
Promos DRF serializers.
"""
from rest_framework import serializers
from decimal import Decimal


class CartItemSerializer(serializers.Serializer):
    """Cart item for promo validation."""
    product_id = serializers.IntegerField(min_value=1)
    qty = serializers.IntegerField(min_value=1)


class PromoValidateRequestSerializer(serializers.Serializer):
    """Request to validate promo code."""
    code = serializers.CharField(max_length=50)
    items = CartItemSerializer(many=True)
    
    def validate_items(self, value):
        """Ensure items list is not empty."""
        if not value:
            raise serializers.ValidationError("Items cannot be empty")
        return value


class PromoInfoSerializer(serializers.Serializer):
    """Promo code information."""
    code = serializers.CharField()
    percent = serializers.DecimalField(max_digits=5, decimal_places=2)


class PromoValidateResponseSerializer(serializers.Serializer):
    """Response from promo validation."""
    is_valid = serializers.BooleanField()
    promo = PromoInfoSerializer(required=False, allow_null=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    error_code = serializers.CharField(required=False, allow_null=True)
    message = serializers.CharField(required=False, allow_null=True)

