# Authentication Microservice

JWT authentication service for IoT Hub microservices architecture.

## Overview

This service handles user authentication and issues JWT tokens with role-based permissions. Other microservices validate these tokens and check permissions to authorize requests.

## Project Structure

```
authentication-microservice/
├── auth_service/              # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── authentication/            # Authentication app
│   ├── management/
│   │   └── commands/
│   │       └── setup_roles.py # Create users and groups
│   ├── services.py            # JWT service
│   ├── views.py               # API views
│   └── urls.py
├── tests/
│   ├── conftest.py            # Pytest fixtures
│   ├── test_endpoints.py      # API endpoint tests
│   └── test_services.py       # Unit tests
├── permissions.json           # Role-to-permissions mapping
├── docker-compose.yml         # PostgreSQL for local dev
├── Dockerfile
├── manage.py
└── requirements.txt
```

## Quick Start

```bash
# 1. Create environment file
cp .env.example .env

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Create users and groups
python manage.py setup_roles

# 6. Start the server
python manage.py runserver 8005
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/auth/login` | POST | Authenticate and get tokens |
| `/v1/auth/refresh` | POST | Refresh access token |
| `/health` | GET | Health check |

### POST /v1/auth/login

Authenticate user and return JWT tokens.

**Request:**
```json
{
  "username": "operator",
  "password": "operator123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer"
}
```

### POST /v1/auth/refresh

Get new access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer"
}
```

### GET /health

**Response:**
```json
{
  "status": "healthy"
}
```

## JWT Payload

Access tokens contain:

```json
{
  "type": "access",
  "sub": "1",
  "username": "operator",
  "email": "operator@example.com",
  "groups": ["Operators"],
  "permissions": ["devices.view", "devices.add", "devices.change", ...],
  "is_staff": true,
  "is_superuser": false,
  "iat": 1234567890,
  "exp": 1234568790
}
```

## Permissions

Permissions are defined in `permissions.json`:

```json
{
  "Operators": [
    "devices.view", "devices.add", "devices.change",
    "events.view", "events.change",
    "rules.view", "rules.add", "rules.change",
    ...
  ],
  "Viewers": [
    "devices.view",
    "events.view",
    "rules.view",
    ...
  ]
}
```

Other microservices check permissions from the JWT:

```python
def has_permission(token_payload, required_permission):
    return required_permission in token_payload.get("permissions", [])

# Usage
if has_permission(token, "devices.add"):
    # allow creating device
```

## Management Commands

### setup_roles

Create admin superuser, groups, and test users.

```bash
# Full setup
python manage.py setup_roles

# Skip specific parts
python manage.py setup_roles --skip-superuser
python manage.py setup_roles --skip-groups
python manage.py setup_roles --skip-users
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Debug mode | `false` |
| `DJANGO_SECRET_KEY` | Django secret key | - |
| `JWT_SECRET_KEY` | JWT signing key | - |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Access token lifetime | `15` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Refresh token lifetime | `7` |
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_DB` | Database name | `iot_microservices` |
| `POSTGRES_USER` | Database user | `iot_user` |
| `POSTGRES_PASSWORD` | Database password | `iot_password` |
| `ADMIN_USERNAME` | Superuser username | `admin` |
| `ADMIN_EMAIL` | Superuser email | `admin@example.com` |
| `ADMIN_PASSWORD` | Superuser password | `admin123` |

## Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=authentication

# Run specific test file
pytest tests/test_endpoints.py
```

## Docker

```bash
# Build image
docker build -t auth-service .

# Run container
docker run -p 8005:8005 --env-file .env auth-service
```
