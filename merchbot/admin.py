"""
Custom Django Admin configuration with dashboard.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta


class MerchBotAdminSite(admin.AdminSite):
    """Custom admin site with dashboard."""
    
    site_header = '🎓 MDIST Merch Shop Admin'
    site_title = 'MerchBot Admin'
    index_title = 'Dashboard'
    
    def get_urls(self):
        """Add custom dashboard URL."""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        """Custom dashboard view with statistics."""
        from catalog.models import Category, Product
        from orders.models import Order
        from promos.models import PromoCode
        
        # Time ranges
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        
        # Orders statistics
        total_orders = Order.objects.count()
        today_orders = Order.objects.filter(created_at__gte=today_start).count()
        week_orders = Order.objects.filter(created_at__gte=week_start).count()
        
        new_orders = Order.objects.filter(status='new').count()
        pending_orders = Order.objects.filter(status__in=['new', 'contacted']).count()
        
        # Revenue statistics
        total_revenue = Order.objects.aggregate(Sum('total'))['total__sum'] or 0
        today_revenue = Order.objects.filter(created_at__gte=today_start).aggregate(Sum('total'))['total__sum'] or 0
        week_revenue = Order.objects.filter(created_at__gte=week_start).aggregate(Sum('total'))['total__sum'] or 0
        
        total_discount = Order.objects.aggregate(Sum('discount_total'))['discount_total__sum'] or 0
        
        # Products statistics
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()
        out_of_stock = Product.objects.filter(quantity=0, is_active=True).count()
        products_on_sale = Product.objects.filter(discount_price__isnull=False, is_active=True).count()
        
        # Categories statistics
        total_categories = Category.objects.count()
        active_categories = Category.objects.filter(is_active=True).count()
        
        # Promo codes
        total_promos = PromoCode.objects.count()
        active_promos = PromoCode.objects.filter(is_active=True).count()
        promo_usage = Order.objects.exclude(promo__isnull=True).count()
        
        # Recent orders
        recent_orders = Order.objects.select_related('promo').prefetch_related('items').order_by('-created_at')[:10]
        
        # Top products (most ordered)
        from orders.models import OrderItem
        top_products = OrderItem.objects.values(
            'product__name'
        ).annotate(
            total_qty=Sum('qty'),
            total_revenue=Sum('line_total')
        ).order_by('-total_qty')[:5]
        
        # Orders by status
        orders_by_status = Order.objects.values('status').annotate(count=Count('id'))
        status_data = {item['status']: item['count'] for item in orders_by_status}
        
        context = {
            **self.each_context(request),
            'total_orders': total_orders,
            'today_orders': today_orders,
            'week_orders': week_orders,
            'new_orders': new_orders,
            'pending_orders': pending_orders,
            'total_revenue': total_revenue,
            'today_revenue': today_revenue,
            'week_revenue': week_revenue,
            'total_discount': total_discount,
            'total_products': total_products,
            'active_products': active_products,
            'out_of_stock': out_of_stock,
            'products_on_sale': products_on_sale,
            'total_categories': total_categories,
            'active_categories': active_categories,
            'total_promos': total_promos,
            'active_promos': active_promos,
            'promo_usage': promo_usage,
            'recent_orders': recent_orders,
            'top_products': top_products,
            'status_data': status_data,
        }
        
        return render(request, 'admin/dashboard.html', context)
    
    def index(self, request, extra_context=None):
        """Override index to show dashboard."""
        return self.dashboard_view(request)


# Create custom admin site instance
admin_site = MerchBotAdminSite(name='merchbot_admin')

