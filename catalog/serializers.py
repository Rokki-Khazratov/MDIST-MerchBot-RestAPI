"""
Catalog DRF serializers.
"""
from rest_framework import serializers
from catalog.models import Category, Product, ImageAsset, ProductImage


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer for CRUD operations."""
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'is_active', 'sort_order']
        read_only_fields = ['id']


class ImageAssetSerializer(serializers.ModelSerializer):
    """Image asset serializer."""
    
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = ImageAsset
        fields = ['id', 'url', 'width', 'height', 'content_type', 'file_size']
        read_only_fields = ['id', 'width', 'height', 'content_type', 'file_size']
    
    def get_url(self, obj):
        """Get absolute URL for image."""
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None


class ProductImageSerializer(serializers.ModelSerializer):
    """Product image through table serializer."""
    
    image = ImageAssetSerializer(read_only=True)
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'sort_order', 'alt_text', 'is_primary']


class ProductListSerializer(serializers.ModelSerializer):
    """Product serializer for list view."""
    
    category = CategorySerializer(read_only=True)
    price_effective = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    thumbnail = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'price', 'discount_price', 'price_effective',
            'category', 'quantity', 'is_active',
            'thumbnail', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_thumbnail(self, obj):
        """Get primary image as thumbnail."""
        primary_image = obj.get_primary_image()
        if primary_image:
            request = self.context.get('request')
            serializer = ImageAssetSerializer(primary_image, context={'request': request})
            return serializer.data
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Product serializer for detail view with all images."""
    
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    price_effective = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    thumbnail = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'price', 'discount_price', 'price_effective',
            'category', 'category_id', 'quantity', 'is_active',
            'thumbnail', 'images', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_thumbnail(self, obj):
        """Get primary image as thumbnail."""
        primary_image = obj.get_primary_image()
        if primary_image:
            request = self.context.get('request')
            serializer = ImageAssetSerializer(primary_image, context={'request': request})
            return serializer.data
        return None
    
    def get_images(self, obj):
        """Get all product images sorted by sort_order."""
        product_images = obj.productimage_set.all().order_by('sort_order')
        request = self.context.get('request')
        return ProductImageSerializer(
            product_images, 
            many=True, 
            context={'request': request}
        ).data


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Product serializer for create/update operations."""
    
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category'
    )
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'price', 'discount_price',
            'category_id', 'quantity', 'is_active'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """Validate product data."""
        if 'discount_price' in data and data['discount_price'] is not None:
            if data['discount_price'] >= data.get('price', 0):
                raise serializers.ValidationError({
                    'discount_price': 'Discount price must be less than regular price'
                })
        return data

