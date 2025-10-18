"""
Category URLs.
"""
from rest_framework.routers import DefaultRouter
from catalog.views import CategoryViewSet

router = DefaultRouter()
router.register(r'', CategoryViewSet, basename='category')

urlpatterns = router.urls
