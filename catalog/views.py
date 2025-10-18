"""
Catalog API views (DRF viewsets).
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from catalog.models import Category, Product
from catalog.serializers import (
    CategorySerializer,
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category CRUD operations.
    
    Endpoints:
    - GET /api/v1/categories/ - List all active categories
    - GET /api/v1/categories/{id}/ - Retrieve category detail
    - POST /api/v1/categories/ - Create new category
    - PUT/PATCH /api/v1/categories/{id}/ - Update category
    - DELETE /api/v1/categories/{id}/ - Delete category
    """
    
    queryset = Category.objects.all().order_by('sort_order', 'name')
    serializer_class = CategorySerializer
    
    def get_queryset(self):
        """Filter to show only active categories for list view."""
        queryset = super().get_queryset()
        
        # For list view, only show active categories by default
        if self.action == 'list':
            show_inactive = self.request.query_params.get('show_inactive', 'false')
            if show_inactive.lower() != 'true':
                queryset = queryset.filter(is_active=True)
        
        return queryset


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD operations.
    
    Endpoints:
    - GET /api/v1/products/ - List products (with filters)
    - GET /api/v1/products/{id}/ - Retrieve product detail
    - POST /api/v1/products/ - Create new product
    - PUT/PATCH /api/v1/products/{id}/ - Update product
    - DELETE /api/v1/products/{id}/ - Delete product
    
    Filters:
    - category: Filter by category ID
    - is_active: Filter by active status
    - search: Search in name and description
    - ordering: Sort by fields (e.g., -created_at, price)
    """
    
    queryset = Product.objects.select_related('category').prefetch_related(
        'productimage_set__image'
    ).all()
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def get_queryset(self):
        """Apply filters to queryset."""
        queryset = super().get_queryset()
        
        # For list view, only show active products by default
        if self.action == 'list':
            show_inactive = self.request.query_params.get('show_inactive', 'false')
            if show_inactive.lower() != 'true':
                queryset = queryset.filter(is_active=True)
        
        return queryset
