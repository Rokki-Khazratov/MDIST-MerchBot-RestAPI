# 🚀 MerchBot Docker Deployment Instructions

## 📋 **Полный план деплоя на сервер**

### **Этап 1: Подготовка сервера**

```bash
# На вашем сервере
cd /root/projects/tests/ecommerce/

# Клонировать репозиторий
git clone https://github.com/Rokki-Khazratov/MDIST-MerchBot-RestAPI.git .

# Или скопировать файлы проекта
# scp -r /path/to/local/project/* root@your-server:/root/projects/tests/ecommerce/
```

### **Этап 2: Настройка переменных окружения**

```bash
# Скопировать файл переменных окружения
cp env.server .env

# Отредактировать .env файл
nano .env
```

**Обязательно измените в .env файле:**

```env
# Замените на ваш IP адрес сервера
SERVER_IP=YOUR_ACTUAL_SERVER_IP

# Сгенерируйте новый SECRET_KEY
SECRET_KEY=your-new-secret-key-here

# Придумайте пароль для базы данных
DB_PASSWORD=your-secure-password

# Обновите URL админки
ADMIN_URL_PREFIX=http://YOUR_SERVER_IP:8000
```

### **Этап 3: Установка Docker (если не установлен)**

```bash
# Обновить систему
apt update && apt upgrade -y

# Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установить Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Добавить пользователя в группу docker
usermod -aG docker root
```

### **Этап 4: Запуск приложения**

```bash
# Сделать скрипт исполняемым
chmod +x deploy.sh

# Запустить деплой
./deploy.sh
```

**Или вручную:**

```bash
# Собрать и запустить контейнеры
docker-compose up --build -d

# Проверить статус
docker-compose ps

# Посмотреть логи
docker-compose logs -f
```

### **Этап 5: Настройка бота**

После запуска приложения:

1. **Откройте админку:** `http://YOUR_SERVER_IP:8000/admin/`
2. **Войдите:** username: `admin`, password: `admin123`
3. **Настройте бота:** `/admin/telegram_bot/botconfig/`
   - Проверьте Bot Token
   - Проверьте Group ID
   - Добавьте Mini App URL (если есть)

### **Этап 6: Тестирование**

```bash
# Проверить API
curl http://YOUR_SERVER_IP:8000/api/v1/products/

# Проверить здоровье
curl http://YOUR_SERVER_IP:8000/health/

# Проверить админку
curl http://YOUR_SERVER_IP:8000/admin/
```

### **Этап 7: Настройка домена (опционально)**

Если хотите использовать домен вместо IP:

1. **Настройте DNS** на ваш IP адрес
2. **Получите SSL сертификат** (Let's Encrypt)
3. **Обновите nginx.conf** для HTTPS
4. **Обновите переменные окружения**

## 🔧 **Управление сервисами**

```bash
# Остановить все сервисы
docker-compose down

# Запустить сервисы
docker-compose up -d

# Перезапустить сервисы
docker-compose restart

# Посмотреть логи
docker-compose logs -f web
docker-compose logs -f bot

# Обновить код
git pull
docker-compose up --build -d
```

## 📊 **Мониторинг**

```bash
# Статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Логи приложения
tail -f logs/django.log
```

## 🚨 **Устранение проблем**

### **Проблема: Контейнеры не запускаются**
```bash
# Проверить логи
docker-compose logs

# Проверить переменные окружения
cat .env

# Пересобрать контейнеры
docker-compose down
docker-compose up --build -d
```

### **Проблема: База данных не подключается**
```bash
# Проверить статус PostgreSQL
docker-compose exec db pg_isready -U merchbot_user -d merchbot_db

# Запустить миграции вручную
docker-compose exec web python manage.py migrate
```

### **Проблема: Бот не работает**
```bash
# Проверить логи бота
docker-compose logs bot

# Проверить конфигурацию бота
docker-compose exec web python manage.py shell -c "
from telegram_bot.models import BotConfig
config = BotConfig.objects.first()
print(f'Bot active: {config.is_active}')
print(f'Token: {config.bot_token[:10]}...')
"
```

## 📱 **Доступ к сервисам**

После успешного деплоя:

- **🌐 API:** `http://YOUR_SERVER_IP:8000/api/v1/`
- **⚙️ Админка:** `http://YOUR_SERVER_IP:8000/admin/`
- **💚 Здоровье:** `http://YOUR_SERVER_IP:8000/health/`
- **📱 Telegram Bot:** Работает автоматически

## 🎉 **Готово!**

Ваш MerchBot теперь работает на сервере с Docker! 

**Домен не обязателен** для начала - можно использовать IP адрес. Позже добавить домен с SSL для webhook.
