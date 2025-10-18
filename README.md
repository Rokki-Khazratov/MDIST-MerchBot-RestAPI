# Merchbot REST API Backend

REST API backend for University Merch Shop Telegram Mini App.

## Tech Stack

- **Python 3.12+**
- **Django 5.1** + **Django REST Framework**
- **Pydantic v2** for DTO validation
- **SQLite** (dev) → **PostgreSQL** (production, later)
- **Timezone**: `Asia/Tashkent`
- **Currency**: UZS (Uzbekistan Som)

## Project Structure

```
merchbot/
├── catalog/          # Products, Categories, Images
├── promos/           # Promo codes
├── orders/           # Orders
└── merchbot/         # Main Django project

apps/
├── models.py         # ORM models (clean, no business logic)
├── dto.py            # Pydantic schemas (API contracts)
├── services.py       # Business logic
├── repos.py          # Complex queries (catalog only)
├── views.py          # DRF views/viewsets
└── admin.py          # Django Admin
```

## Setup & Installation

### 1. Create Virtual Environment

```bash
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (for Admin Panel)

```bash
python manage.py createsuperuser
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Server will be available at: `http://127.0.0.1:8000/`

## API Endpoints

### Health Check

- `GET /health/` - Service health status (root)
- `GET /api/v1/health/` - Service health status (API v1)

### Catalog ✅ READY

- `GET /api/v1/categories/` - List categories
- `GET /api/v1/categories/{id}/` - Category detail
- `POST /api/v1/categories/` - Create category
- `PUT/PATCH /api/v1/categories/{id}/` - Update category
- `DELETE /api/v1/categories/{id}/` - Delete category
- `GET /api/v1/products/` - List products (with filters, search, pagination)
- `GET /api/v1/products/{id}/` - Product detail
- `POST /api/v1/products/` - Create product
- `PUT/PATCH /api/v1/products/{id}/` - Update product
- `DELETE /api/v1/products/{id}/` - Delete product

### Promo Codes (Coming in Iteration 5)

- `POST /api/v1/promos/validate` - Validate promo code and calculate discount

### Orders (Coming in Iteration 5)

- `POST /api/v1/orders/` - Create order
- `GET /api/v1/orders/{id}/` - Get order details

### API Documentation

- Swagger UI: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- Schema: `http://127.0.0.1:8000/api/schema/`

## Admin Panel

Access Django Admin at: `http://127.0.0.1:8000/admin/`

Login with superuser credentials created in step 4.

## Testing

Run tests with pytest:

```bash
pytest
```

With coverage:

```bash
pytest --cov=catalog --cov=promos --cov=orders
```

## Development Status

### ✅ Iteration 1: Scaffold (COMPLETED)

- [x] Django project setup
- [x] Apps created (catalog, promos, orders)
- [x] Settings configured (timezone, media, constants)
- [x] Base models implemented
- [x] Initial migrations
- [x] Health endpoint

### 🚧 Iteration 2: Domain Models + Admin (TODO)

- [ ] Complete model relationships (FK, M2M, through tables)
- [ ] Model constraints and validations
- [ ] Full Django Admin with inlines, filters, actions
- [ ] Test fixtures

### 📋 Iteration 3: DTO + Services (TODO)

- [ ] Pydantic schemas for all endpoints
- [ ] Service layer (PricingService, PromoService, OrderService)
- [ ] Unit tests

### 📋 Iteration 4: Catalog API (TODO)

- [ ] Catalog repository layer
- [ ] DRF viewsets for categories and products
- [ ] Filters, search, sorting, pagination
- [ ] Integration tests

### 📋 Iteration 5: Promo + Orders API (TODO)

- [ ] Promo validation endpoint
- [ ] Order creation endpoint
- [ ] Order detail endpoint
- [ ] Integration tests

### 📋 Iteration 6: Polish (TODO)

- [ ] Exception handler improvements
- [ ] API documentation
- [ ] Test coverage >80%
- [ ] Performance optimization

## Environment Variables

For production, create `.env` file:

```env
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/merchbot
ALLOWED_HOSTS=yourdomain.com
```

## Contributing

This is a university project. For questions or issues, contact the development team.

## License

Proprietary - University Merch Shop Project
