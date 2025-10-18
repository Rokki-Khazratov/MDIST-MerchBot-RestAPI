"""
Orders business logic (order creation, snapshots, calculations).
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from django.db import transaction
from django.conf import settings

from catalog.models import Product
from orders.models import Order, OrderItem
from promos.services import PromoService
from merchbot.exceptions import (
    EmptyCartError,
    ProductNotFoundError,
    ProductInactiveError
)


class OrderService:
    """Service for order creation and management."""
    
    @staticmethod
    def deduplicate_items(items: List[Dict]) -> List[Dict]:
        """
        Deduplicate cart items by summing quantities for same product_id.
        
        Args:
            items: List of {'product_id': int, 'qty': int}
            
        Returns:
            List[Dict]: Deduplicated items
        """
        # Group by product_id and sum quantities
        qty_by_product = defaultdict(int)
        for item in items:
            qty_by_product[item['product_id']] += item['qty']
        
        # Convert back to list
        return [
            {'product_id': product_id, 'qty': qty}
            for product_id, qty in qty_by_product.items()
        ]
    
    @staticmethod
    def validate_and_get_products(items: List[Dict]) -> Dict[int, Product]:
        """
        Validate cart items and return products.
        
        Args:
            items: List of {'product_id': int, 'qty': int}
            
        Returns:
            Dict[int, Product]: Mapping of product_id to Product
            
        Raises:
            EmptyCartError: Cart is empty
            ProductNotFoundError: Product not found
            ProductInactiveError: Product is not active
        """
        if not items:
            raise EmptyCartError()
        
        # Get all product IDs
        product_ids = [item['product_id'] for item in items]
        
        # Fetch all products in one query
        products = Product.objects.filter(id__in=product_ids).select_related('category')
        products_by_id = {p.id: p for p in products}
        
        # Validate all products exist and are active
        for item in items:
            product_id = item['product_id']
            
            if product_id not in products_by_id:
                raise ProductNotFoundError(product_id)
            
            if not products_by_id[product_id].is_active:
                raise ProductInactiveError(product_id)
        
        return products_by_id
    
    @staticmethod
    def calculate_subtotal(items: List[Dict], products_by_id: Dict[int, Product]) -> Decimal:
        """
        Calculate subtotal from cart items.
        
        Args:
            items: List of {'product_id': int, 'qty': int}
            products_by_id: Mapping of product_id to Product
            
        Returns:
            Decimal: Subtotal amount
        """
        subtotal = Decimal('0.00')
        
        for item in items:
            product = products_by_id[item['product_id']]
            price_effective = product.price_effective
            qty = item['qty']
            line_total = price_effective * qty
            subtotal += line_total
        
        return subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    @transaction.atomic
    def create_order(
        items: List[Dict],
        full_name: str,
        phone_number: str,
        payment_method: str,
        telegram_username: Optional[str] = None,
        promo_code: Optional[str] = None,
        comment: Optional[str] = None
    ) -> Order:
        """
        Create order with items (in transaction).
        
        Args:
            items: List of {'product_id': int, 'qty': int}
            full_name: Customer full name
            phone_number: Customer phone
            payment_method: Payment method ('cash' or 'card')
            telegram_username: Optional telegram username
            promo_code: Optional promo code
            comment: Optional comment
            
        Returns:
            Order: Created order
            
        Raises:
            EmptyCartError, ProductNotFoundError, ProductInactiveError,
            PromoNotFoundError, PromoInactiveError, PromoExpiredError
        """
        # Step 1: Deduplicate items
        items = OrderService.deduplicate_items(items)
        
        # Step 2: Validate products and get them
        products_by_id = OrderService.validate_and_get_products(items)
        
        # Step 3: Calculate subtotal
        subtotal = OrderService.calculate_subtotal(items, products_by_id)
        
        # Step 4: Apply promo code if provided
        promo = None
        discount_total = Decimal('0.00')
        total = subtotal
        
        if promo_code:
            promo, discount_total, total = PromoService.validate_and_calculate(
                promo_code,
                subtotal
            )
        
        # Step 5: Create Order
        order = Order.objects.create(
            full_name=full_name,
            phone_number=phone_number,
            telegram_username=telegram_username,
            payment_method=payment_method,
            promo=promo,
            subtotal=subtotal,
            discount_total=discount_total,
            total=total,
            comment=comment,
            status=Order.STATUS_NEW
        )
        
        # Step 6: Create OrderItems with snapshots
        order_items = []
        for item in items:
            product = products_by_id[item['product_id']]
            price_snapshot = product.price_effective
            qty = item['qty']
            line_total = (price_snapshot * qty).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP
            )
            
            order_item = OrderItem(
                order=order,
                product=product,
                name_snapshot=product.name,
                price_snapshot=price_snapshot,
                qty=qty,
                line_total=line_total
            )
            order_items.append(order_item)
        
        # Bulk create order items
        OrderItem.objects.bulk_create(order_items)
        
        return order
