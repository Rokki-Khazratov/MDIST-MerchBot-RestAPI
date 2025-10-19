"""
Integration tests for Telegram Bot views.
"""
import pytest
import json
from unittest.mock import patch, AsyncMock, Mock
from django.test import TestCase, Client
from django.urls import reverse

from telegram_bot.models import BotConfig


@pytest.mark.django_db
class TestWebhookView(TestCase):
    """Tests for webhook endpoint."""
    
    def setUp(self):
        """Setup test data."""
        self.client = Client()
        self.bot_config = BotConfig.objects.create(
            bot_token='123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            notification_group_id='-1001234567890',
            webhook_url='https://example.com/telegram/webhook/',
            is_active=True
        )
    
    @patch('telegram_bot.services.webhook.WebhookService.process_update')
    def test_webhook_success(self, mock_process):
        """Test webhook receiving update successfully."""
        # Mock async function
        async def mock_process_update(data):
            return {'status': 'ok', 'message': 'Update processed'}
        
        with patch('asyncio.new_event_loop') as mock_loop:
            mock_event_loop = Mock()
            mock_event_loop.run_until_complete.return_value = {'status': 'ok', 'message': 'Update processed'}
            mock_loop.return_value = mock_event_loop
            
            update_data = {
                'update_id': 123456,
                'message': {
                    'message_id': 1,
                    'from': {
                        'id': 123,
                        'first_name': 'Test'
                    },
                    'chat': {
                        'id': 123,
                        'type': 'private'
                    },
                    'date': 1234567890,
                    'text': '/start'
                }
            }
            
            response = self.client.post(
                '/telegram/webhook/',
                data=json.dumps(update_data),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'ok'
    
    def test_webhook_invalid_data(self):
        """Test webhook with invalid data."""
        response = self.client.post(
            '/telegram/webhook/',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 500


@pytest.mark.django_db
class TestWebhookManagementViews(TestCase):
    """Tests for webhook management endpoints."""
    
    def setUp(self):
        """Setup test data."""
        self.client = Client()
        self.bot_config = BotConfig.objects.create(
            bot_token='123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11',
            notification_group_id='-1001234567890',
            is_active=True
        )
    
    @patch('telegram_bot.services.telegram.TelegramService.set_webhook')
    def test_setup_webhook_success(self, mock_set_webhook):
        """Test setting up webhook successfully."""
        async def mock_set_webhook_async(url):
            return True
        
        with patch('asyncio.new_event_loop') as mock_loop:
            mock_event_loop = Mock()
            mock_event_loop.run_until_complete.return_value = True
            mock_loop.return_value = mock_event_loop
            
            response = self.client.post(
                '/telegram/setup-webhook/',
                data=json.dumps({
                    'webhook_url': 'https://example.com/telegram/webhook/'
                }),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            
            # Check config was updated
            config = BotConfig.objects.first()
            assert config.webhook_url == 'https://example.com/telegram/webhook/'
    
    def test_setup_webhook_missing_url(self):
        """Test setting up webhook without URL."""
        response = self.client.post(
            '/telegram/setup-webhook/',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
    
    @patch('telegram_bot.services.telegram.TelegramService.get_webhook_info')
    def test_webhook_info(self, mock_get_info):
        """Test getting webhook info."""
        async def mock_get_info_async():
            return {
                'url': 'https://example.com/telegram/webhook/',
                'has_custom_certificate': False,
                'pending_update_count': 0
            }
        
        with patch('asyncio.new_event_loop') as mock_loop:
            mock_event_loop = Mock()
            mock_event_loop.run_until_complete.return_value = {
                'url': 'https://example.com/telegram/webhook/',
                'has_custom_certificate': False,
                'pending_update_count': 0
            }
            mock_loop.return_value = mock_event_loop
            
            response = self.client.get('/telegram/webhook-info/')
            
            assert response.status_code == 200
            data = response.json()
            assert 'url' in data
    
    @patch('telegram_bot.services.telegram.TelegramService.delete_webhook')
    def test_delete_webhook(self, mock_delete):
        """Test deleting webhook."""
        self.bot_config.webhook_url = 'https://example.com/telegram/webhook/'
        self.bot_config.save()
        
        async def mock_delete_async():
            return True
        
        with patch('asyncio.new_event_loop') as mock_loop:
            mock_event_loop = Mock()
            mock_event_loop.run_until_complete.return_value = True
            mock_loop.return_value = mock_event_loop
            
            response = self.client.post('/telegram/delete-webhook/')
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            
            # Check config was updated
            config = BotConfig.objects.first()
            assert config.webhook_url is None


