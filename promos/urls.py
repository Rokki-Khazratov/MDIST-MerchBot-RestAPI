"""
Promos URL configuration.
"""
from django.urls import path
from promos.views import PromoValidateView

urlpatterns = [
    path('validate/', PromoValidateView.as_view(), name='promo-validate'),
]
