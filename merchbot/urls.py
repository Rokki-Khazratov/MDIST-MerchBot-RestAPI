"""
URL configuration for merchbot project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
# from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView  # Uncomment after installing

from merchbot.views import health_check


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
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

