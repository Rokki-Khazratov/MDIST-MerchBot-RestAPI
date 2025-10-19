"""
Tests for Telegram Bot signals.
"""
import pytest
from unittest.mock import patch, Mock
from django.test import TestCase
from decimal import Decimal

from orders.models import Order
from telegram_bot.models import BotConfig, GroupNotification
from telegram_bot.exceptions import NotificationFailedError


@pytest.mark.django_db
class TestOrderSignals(TestCase):
    """Tests for order creation signals."""
    
    def setUp(self):
        """Setup test data."""
        # Create bot config
        self.bot_config = BotConfig.objects.create(
            bot_token='123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            notification_group_id='-1001234567890',
            is_active=True
        )
        
        # Create test data
        from catalog.models import Category, Product
        
        category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('100.00'),
            quantity=10,
            category=category
        )
    
    @patch('telegram_bot.services.notification.NotificationService.send_order_notification_sync')
    def test_order_creation_sends_notification(self, mock_send):
        """Test that creating order sends notification."""
        mock_notification = Mock()
        mock_notification.message_id = '12345'
        mock_notification.status = GroupNotification.STATUS_SENT
        mock_send.return_value = mock_notification
        
        # Create order
        order = Order.objects.create(
            full_name='Test User',
            phone_number='+998901234567',
            payment_method='cash',
            subtotal=Decimal('100.00'),
            discount_total=Decimal('0.00'),
            total=Decimal('100.00')
        )
        
        # Check notification was sent
        mock_send.assert_called_once_with(order)
    
    @patch('telegram_bot.services.notification.NotificationService.send_order_notification_sync')
    def test_order_update_does_not_send_notification(self, mock_send):
        """Test that updating order does not send notification."""
        # Create order
        order = Order.objects.create(
            full_name='Test User',
            phone_number='+998901234567',
            payment_method='cash',
            subtotal=Decimal('100.00'),
            discount_total=Decimal('0.00'),
            total=Decimal('100.00')
        )
        
        mock_send.reset_mock()
        
        # Update order
        order.status = Order.STATUS_DELIVERED
        order.save()
        
        # Check notification was NOT sent
        mock_send.assert_not_called()
    
    @patch('telegram_bot.services.notification.NotificationService.send_order_notification_sync')
    def test_notification_failure_does_not_break_order_creation(self, mock_send):
        """Test that notification failure doesn't prevent order creation."""
        mock_send.side_effect = NotificationFailedError('Test error')
        
        # Create order - should not raise exception
        order = Order.objects.create(
            full_name='Test User',
            phone_number='+998901234567',
            payment_method='cash',
            subtotal=Decimal('100.00'),
            discount_total=Decimal('0.00'),
            total=Decimal('100.00')
        )
        
        # Order should be created successfully
        assert order.id is not None
        assert Order.objects.filter(id=order.id).exists()
    
    @patch('telegram_bot.services.notification.NotificationService.send_order_notification_sync')
    def test_bot_inactive_does_not_break_order_creation(self, mock_send):
        """Test that inactive bot doesn't prevent order creation."""
        # Make bot inactive
        self.bot_config.is_active = False
        self.bot_config.save()
        
        from telegram_bot.exceptions import BotInactiveError
        mock_send.side_effect = BotInactiveError()
        
        # Create order - should not raise exception
        order = Order.objects.create(
            full_name='Test User',
            phone_number='+998901234567',
            payment_method='cash',
            subtotal=Decimal('100.00'),
            discount_total=Decimal('0.00'),
            total=Decimal('100.00')
        )
        
        # Order should be created successfully
        assert order.id is not None
        assert Order.objects.filter(id=order.id).exists()


