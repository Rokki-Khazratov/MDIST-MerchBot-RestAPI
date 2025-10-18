"""
Promos API views.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal

from promos.serializers import PromoValidateRequestSerializer
from promos.services import PromoService
from orders.services import OrderService
from merchbot.exceptions import (
    PromoNotFoundError,
    PromoInactiveError,
    PromoExpiredError,
    ProductNotFoundError,
    ProductInactiveError,
    EmptyCartError
)


class PromoValidateView(APIView):
    """
    POST /api/v1/promos/validate
    
    Validate promo code and calculate discount.
    """
    
    def post(self, request):
        """Validate promo code and return discount calculation."""
        # Validate request
        serializer = PromoValidateRequestSerializer(data=request.data)
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
        code = data['code']
        items = data['items']
        
        try:
            # Deduplicate items
            items = OrderService.deduplicate_items(items)
            
            # Validate products and calculate subtotal
            products_by_id = OrderService.validate_and_get_products(items)
            subtotal = OrderService.calculate_subtotal(items, products_by_id)
            
            # Validate promo and calculate discount
            promo, discount_total, total = PromoService.validate_and_calculate(
                code,
                subtotal
            )
            
            # Success response
            return Response({
                'is_valid': True,
                'promo': {
                    'code': promo.code,
                    'percent': str(promo.percent)
                },
                'subtotal': str(subtotal),
                'discount': str(discount_total),
                'total': str(total)
            })
        
        except (PromoNotFoundError, PromoInactiveError, PromoExpiredError) as e:
            # Invalid promo - return calculated subtotal without discount
            try:
                items = OrderService.deduplicate_items(items)
                products_by_id = OrderService.validate_and_get_products(items)
                subtotal = OrderService.calculate_subtotal(items, products_by_id)
            except:
                subtotal = Decimal('0.00')
            
            return Response({
                'is_valid': False,
                'error_code': e.error_code,
                'message': e.message,
                'subtotal': str(subtotal),
                'discount': '0.00',
                'total': str(subtotal)
            })
        
        except (ProductNotFoundError, ProductInactiveError, EmptyCartError) as e:
            # Product validation error
            return Response(
                {
                    'error_code': e.error_code,
                    'message': e.message
                },
                status=status.HTTP_400_BAD_REQUEST
            )
