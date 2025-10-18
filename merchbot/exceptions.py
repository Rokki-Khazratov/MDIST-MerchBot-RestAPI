"""
Custom exception handler for unified error responses.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns unified error format:
    
    {
        "error_code": "ERROR_CODE",
        "message": "Human-readable message",
        "details": {}  # Optional field-specific errors
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Transform DRF error format to our unified format
        custom_response_data = {}
        
        # Determine error code
        if response.status_code == status.HTTP_404_NOT_FOUND:
            custom_response_data['error_code'] = 'NOT_FOUND'
            custom_response_data['message'] = 'Resource not found'
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data['error_code'] = 'VALIDATION_ERROR'
            custom_response_data['message'] = 'Validation error'
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            custom_response_data['error_code'] = 'FORBIDDEN'
            custom_response_data['message'] = 'Permission denied'
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            custom_response_data['error_code'] = 'UNAUTHORIZED'
            custom_response_data['message'] = 'Authentication required'
        else:
            custom_response_data['error_code'] = 'ERROR'
            custom_response_data['message'] = 'An error occurred'
        
        # Add details if present
        if isinstance(response.data, dict):
            # If there's a 'detail' field, use it as message
            if 'detail' in response.data:
                custom_response_data['message'] = str(response.data['detail'])
            else:
                # Otherwise, include all fields as details
                custom_response_data['details'] = response.data
        elif isinstance(response.data, list):
            custom_response_data['details'] = {'errors': response.data}
        
        response.data = custom_response_data
    
    return response


class BusinessLogicError(Exception):
    """
    Base exception for business logic errors.
    
    Usage:
        raise BusinessLogicError('PRODUCT_INACTIVE', 'Product is not active')
    """
    def __init__(self, error_code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


# Promo-related exceptions
class PromoNotFoundError(BusinessLogicError):
    """Promo code not found."""
    def __init__(self):
        super().__init__('PROMO_NOT_FOUND', 'Promo code not found')


class PromoInactiveError(BusinessLogicError):
    """Promo code is inactive."""
    def __init__(self):
        super().__init__('PROMO_INACTIVE', 'Promo code is not active')


class PromoExpiredError(BusinessLogicError):
    """Promo code has expired."""
    def __init__(self):
        super().__init__('PROMO_EXPIRED', 'Promo code has expired')


# Product-related exceptions
class ProductNotFoundError(BusinessLogicError):
    """Product not found."""
    def __init__(self, product_id: int):
        super().__init__(
            'PRODUCT_NOT_FOUND',
            f'Product with ID {product_id} not found'
        )


class ProductInactiveError(BusinessLogicError):
    """Product is not active."""
    def __init__(self, product_id: int):
        super().__init__(
            'PRODUCT_INACTIVE',
            f'Product with ID {product_id} is not active'
        )


# Order-related exceptions
class EmptyCartError(BusinessLogicError):
    """Cart is empty."""
    def __init__(self):
        super().__init__('EMPTY_CART', 'Cart cannot be empty')

