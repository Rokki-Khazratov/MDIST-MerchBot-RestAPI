"""
URL configuration for merchbot project.
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView  # Uncomment after installing

from merchbot.views import health_check
from merchbot.admin import admin_site

# Register all models with custom admin site
from catalog.admin import CategoryAdmin, ImageAssetAdmin, ProductAdmin
from catalog.models import Category, ImageAsset, Product
from promos.admin import PromoCodeAdmin
from promos.models import PromoCode
from orders.admin import OrderAdmin, OrderItemAdmin
from orders.models import Order, OrderItem

admin_site.register(Category, CategoryAdmin)
admin_site.register(ImageAsset, ImageAssetAdmin)
admin_site.register(Product, ProductAdmin)
admin_site.register(PromoCode, PromoCodeAdmin)
admin_site.register(Order, OrderAdmin)
admin_site.register(OrderItem, OrderItemAdmin)


urlpatterns = [
    # Admin with custom dashboard
    path('admin/', admin_site.urls),
    
    # Health check
    path('health/', health_check, name='health-check'),
    
    # API v1
    path('api/v1/', include([
        path('health/', health_check, name='api-health-check'),
        path('categories/', include('catalog.urls.categories')),
        path('products/', include('catalog.urls.products')),
        path('promos/', include('promos.urls')),
        path('orders/', include('orders.urls')),
    ])),
    
    # Telegram Bot
    path('telegram/', include('telegram_bot.urls')),
    
    # API Documentation (uncomment after installing drf-spectacular)
    # path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Django Debug Toolbar (uncomment after installing dependencies)
    # urlpatterns += [
    #     path('__debug__/', include('debug_toolbar.urls')),
    # ]

