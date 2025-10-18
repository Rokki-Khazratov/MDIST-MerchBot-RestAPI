"""
Orders DRF serializers.
"""
from rest_framework import serializers
from orders.models import Order, OrderItem
from catalog.models import Product


class OrderItemCreateSerializer(serializers.Serializer):
    """Order item for order creation."""
    product_id = serializers.IntegerField(min_value=1)
    qty = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    """Request to create order."""
    items = OrderItemCreateSerializer(many=True)
    full_name = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=20)
    telegram_username = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=['cash', 'card'])
    promo_code = serializers.CharField(max_length=50, required=False, allow_null=True, allow_blank=True)
    comment = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    def validate_items(self, value):
        """Ensure items list is not empty."""
        if not value:
            raise serializers.ValidationError("Items cannot be empty")
        return value


class OrderCreateResponseSerializer(serializers.Serializer):
    """Response after order creation."""
    order_id = serializers.IntegerField()
    status = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    created_at = serializers.DateTimeField()


class PromoSerializer(serializers.Serializer):
    """Promo info in order."""
    code = serializers.CharField()
    percent = serializers.DecimalField(max_digits=5, decimal_places=2)


class OrderItemSerializer(serializers.ModelSerializer):
    """Order item with snapshot data."""
    product_id = serializers.IntegerField(source='product.id')
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'product_id', 'name_snapshot', 'price_snapshot',
            'qty', 'line_total', 'thumbnail_url'
        ]
    
    def get_thumbnail_url(self, obj):
        """Get current thumbnail URL of product."""
        try:
            product = obj.product
            primary_image = product.get_primary_image()
            if primary_image and primary_image.file:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(primary_image.file.url)
                return primary_image.file.url
        except:
            pass
        return None


class OrderListSerializer(serializers.ModelSerializer):
    """Order list item with basic information."""
    promo = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'status', 'full_name', 'phone_number', 'payment_method',
            'promo', 'subtotal', 'discount_total', 'total', 'items_count',
            'created_at'
        ]
    
    def get_promo(self, obj):
        """Get promo code if used."""
        if obj.promo:
            return obj.promo.code
        return None
    
    def get_items_count(self, obj):
        """Get count of items in order."""
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Order detail with all information."""
    promo = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'status', 'full_name', 'phone_number', 'telegram_username',
            'payment_method', 'promo', 'subtotal', 'discount_total', 'total',
            'comment', 'items', 'created_at', 'updated_at'
        ]
    
    def get_promo(self, obj):
        """Get promo information if used."""
        if obj.promo:
            return {
                'code': obj.promo.code,
                'percent': obj.promo.percent
            }
        return None

