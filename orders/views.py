"""
Orders API views.
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from orders.models import Order
from orders.serializers import (
    OrderCreateSerializer,
    OrderCreateResponseSerializer,
    OrderListSerializer,
    OrderDetailSerializer
)
from orders.services import OrderService
from merchbot.exceptions import (
    EmptyCartError,
    ProductNotFoundError,
    ProductInactiveError,
    PromoNotFoundError,
    PromoInactiveError,
    PromoExpiredError
)


class OrderViewSet(viewsets.GenericViewSet):
    """
    Orders ViewSet.
    
    GET /api/v1/orders/ - List all orders
    POST /api/v1/orders/ - Create order
    GET /api/v1/orders/{id}/ - Get order details
    """
    queryset = Order.objects.all().prefetch_related(
        'items__product__images'
    ).select_related('promo')
    serializer_class = OrderDetailSerializer
    
    def list(self, request):
        """List all orders."""
        queryset = self.get_queryset().order_by('-created_at')
        serializer = OrderListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    def create(self, request):
        """Create new order."""
        # Validate request
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    'error_code': 'VALIDATION_ERROR',
                    'message': 'Invalid request data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.validated_data
        
        try:
            # Create order via service
            order = OrderService.create_order(
                items=data['items'],
                full_name=data['full_name'],
                phone_number=data['phone_number'],
                telegram_username=data.get('telegram_username'),
                payment_method=data['payment_method'],
                promo_code=data.get('promo_code'),
                comment=data.get('comment')
            )
            
            # Return success response
            response_data = {
                'order_id': order.id,
                'status': order.status,
                'subtotal': str(order.subtotal),
                'discount_total': str(order.discount_total),
                'total': str(order.total),
                'created_at': order.created_at.isoformat()
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        except (
            EmptyCartError,
            ProductNotFoundError,
            ProductInactiveError,
            PromoNotFoundError,
            PromoInactiveError,
            PromoExpiredError
        ) as e:
            return Response(
                {
                    'error_code': e.error_code,
                    'message': e.message
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def retrieve(self, request, pk=None):
        """Get order details by ID."""
        try:
            order = self.get_queryset().get(pk=pk)
            serializer = OrderDetailSerializer(order, context={'request': request})
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response(
                {
                    'error_code': 'ORDER_NOT_FOUND',
                    'message': f'Order with ID {pk} not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )
