"""
Unit tests for Telegram Bot services.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from django.test import TestCase
from decimal import Decimal

from telegram.error import TelegramError

from orders.models import Order
from telegram_bot.models import BotConfig, GroupNotification
from telegram_bot.services import TelegramService, NotificationService
from telegram_bot.exceptions import (
    BotNotConfiguredError,
    BotInactiveError,
    NotificationFailedError
)


@pytest.mark.django_db
class TestTelegramService(TestCase):
    """Tests for TelegramService."""
    
    def setUp(self):
        """Setup test data."""
        self.bot_config = BotConfig.objects.create(
            bot_token='123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            notification_group_id='-1001234567890',
            is_active=True
        )
    
    def test_get_bot_config_success(self):
        """Test getting bot config successfully."""
        config = TelegramService.get_bot_config()
        assert config == self.bot_config
        assert config.is_active is True
    
    def test_get_bot_config_not_configured(self):
        """Test error when bot is not configured."""
        BotConfig.objects.all().delete()
        
        with pytest.raises(BotNotConfiguredError):
            TelegramService.get_bot_config()
    
    def test_get_bot_config_inactive(self):
        """Test error when bot is inactive."""
        self.bot_config.is_active = False
        self.bot_config.save()
        
        with pytest.raises(BotInactiveError):
            TelegramService.get_bot_config()
    
    def test_get_bot(self):
        """Test getting Bot instance."""
        bot = TelegramService.get_bot()
        assert bot.token == self.bot_config.bot_token
    
    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test sending message successfully."""
        with patch('telegram_bot.services.telegram.Bot') as MockBot:
            mock_bot = MockBot.return_value
            mock_message = Mock()
            mock_message.message_id = 12345
            mock_bot.send_message = AsyncMock(return_value=mock_message)
            
            # Need to patch get_bot
            with patch.object(TelegramService, 'get_bot', return_value=mock_bot):
                message_id = await TelegramService.send_message(
                    chat_id='-1001234567890',
                    text='Test message'
                )
                
                assert message_id == 12345
                mock_bot.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message_failure(self):
        """Test sending message failure."""
        with patch('telegram_bot.services.telegram.Bot') as MockBot:
            mock_bot = MockBot.return_value
            mock_bot.send_message = AsyncMock(side_effect=TelegramError('Test error'))
            
            with patch.object(TelegramService, 'get_bot', return_value=mock_bot):
                with pytest.raises(TelegramError):
                    await TelegramService.send_message(
                        chat_id='-1001234567890',
                        text='Test message'
                    )


@pytest.mark.django_db
class TestNotificationService(TestCase):
    """Tests for NotificationService."""
    
    def setUp(self):
        """Setup test data."""
        # Create bot config
        self.bot_config = BotConfig.objects.create(
            bot_token='123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            notification_group_id='-1001234567890',
            is_active=True
        )
        
        # Create test order
        from catalog.models import Category, Product
        from orders.models import OrderItem
        
        category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            description='Test description',
            price=Decimal('100.00'),
            quantity=10,
            category=category
        )
        
        self.order = Order.objects.create(
            full_name='Test User',
            phone_number='+998901234567',
            telegram_username='testuser',
            payment_method='cash',
            subtotal=Decimal('200.00'),
            discount_total=Decimal('0.00'),
            total=Decimal('200.00')
        )
        
        OrderItem.objects.create(
            order=self.order,
            product=product,
            quantity=2,
            price_snapshot=Decimal('100.00')
        )
    
    def test_format_order_message(self):
        """Test formatting order message."""
        message = NotificationService.format_order_message(self.order)
        
        assert f'НОВЫЙ ЗАКАЗ #{self.order.id}' in message
        assert 'Test User' in message
        assert '+998901234567' in message
        assert '@testuser' in message
        assert 'Test Product' in message
        assert '200' in message  # Total
    
    @pytest.mark.asyncio
    async def test_send_order_notification_success(self):
        """Test sending order notification successfully."""
        with patch.object(TelegramService, 'send_message', new=AsyncMock(return_value=12345)):
            notification = await NotificationService.send_order_notification(self.order)
            
            assert notification.status == GroupNotification.STATUS_SENT
            assert notification.message_id == '12345'
            assert notification.order == self.order
    
    @pytest.mark.asyncio
    async def test_send_order_notification_failure(self):
        """Test sending order notification failure."""
        with patch.object(TelegramService, 'send_message', new=AsyncMock(side_effect=TelegramError('Test error'))):
            with pytest.raises(NotificationFailedError):
                await NotificationService.send_order_notification(self.order)
            
            # Check notification was saved with error
            notification = GroupNotification.objects.get(order=self.order)
            assert notification.status == GroupNotification.STATUS_FAILED
            assert 'Test error' in notification.error_message
    
    def test_send_order_notification_sync(self):
        """Test synchronous wrapper for sending notification."""
        with patch.object(NotificationService, 'send_order_notification', new=AsyncMock(return_value=Mock())):
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop.return_value.run_until_complete.return_value = Mock()
                
                result = NotificationService.send_order_notification_sync(self.order)
                assert result is not None


