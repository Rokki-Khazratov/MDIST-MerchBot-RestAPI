#!/bin/bash

# MerchBot Deployment Script
set -e

echo "🚀 Starting MerchBot deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found! Please create it from env.example"
    exit 1
fi

# Load environment variables
print_status "Loading environment variables..."
source .env

# Check required environment variables
required_vars=("SECRET_KEY" "DB_PASSWORD" "TELEGRAM_BOT_TOKEN" "TELEGRAM_GROUP_ID" "SERVER_IP")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "Required environment variable $var is not set!"
        exit 1
    fi
done

print_success "Environment variables loaded successfully"

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down || true

# Remove old images (optional)
print_warning "Removing old images..."
docker-compose down --rmi all || true

# Build and start services
print_status "Building and starting services..."
docker-compose up --build -d

# Wait for services to be healthy
print_status "Waiting for services to be ready..."
sleep 30

# Check if services are running
print_status "Checking service status..."
docker-compose ps

# Run database migrations
print_status "Running database migrations..."
docker-compose exec web python manage.py migrate

# Create superuser
print_status "Creating superuser..."
docker-compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"

# Collect static files
print_status "Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput

# Setup bot configuration
print_status "Setting up bot configuration..."
docker-compose exec web python manage.py shell -c "
from telegram_bot.models import BotConfig
config, created = BotConfig.objects.get_or_create(
    defaults={
        'bot_token': '$TELEGRAM_BOT_TOKEN',
        'notification_group_id': '$TELEGRAM_GROUP_ID',
        'mini_app_url': '${TELEGRAM_MINI_APP_URL:-https://t.me/your_bot/app}',
        'is_active': True
    }
)
if not created:
    config.bot_token = '$TELEGRAM_BOT_TOKEN'
    config.notification_group_id = '$TELEGRAM_GROUP_ID'
    config.mini_app_url = '${TELEGRAM_MINI_APP_URL:-https://t.me/your_bot/app}'
    config.is_active = True
    config.save()
print('Bot configuration updated successfully')
"

# Show final status
print_success "Deployment completed successfully!"
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo "🌐 Access URLs:"
echo "  - API: http://$SERVER_IP:8000/api/v1/"
echo "  - Admin: http://$SERVER_IP:8000/admin/"
echo "  - Health: http://$SERVER_IP:8000/health/"
echo ""
echo "📱 Bot Configuration:"
echo "  - Bot Token: ${TELEGRAM_BOT_TOKEN:0:10}..."
echo "  - Group ID: $TELEGRAM_GROUP_ID"
echo "  - Mini App URL: ${TELEGRAM_MINI_APP_URL:-Not set}"
echo ""
echo "🔑 Admin Credentials:"
echo "  - Username: admin"
echo "  - Password: admin123"
echo ""
print_warning "Please change the admin password after first login!"
echo ""
print_success "MerchBot is now running! 🎉"
