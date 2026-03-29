import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from django.conf import settings

# Load permissions from JSON file
PERMISSIONS_FILE = Path(settings.BASE_DIR) / "permissions.json"


def load_role_permissions() -> dict:
    """Load role permissions from JSON file."""
    if PERMISSIONS_FILE.exists():
        with open(PERMISSIONS_FILE) as f:
            return json.load(f)
    return {}


def get_permissions_for_user(user) -> list[str]:
    """Get all permissions for a user based on their groups."""
    role_permissions = load_role_permissions()
    permissions = set()

    # Superusers get all permissions
    if user.is_superuser:
        for perms in role_permissions.values():
            permissions.update(perms)
        return sorted(permissions)

    # Get permissions from user's groups
    user_groups = user.groups.values_list("name", flat=True)
    for group_name in user_groups:
        if group_name in role_permissions:
            permissions.update(role_permissions[group_name])

    return sorted(permissions)


class JWTService:
    """Service for creating and validating JWT tokens."""

    @staticmethod
    def create_access_token(user) -> str:
        """Create an access token for the user."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_LIFETIME_MINUTES)

        payload = {
            "type": "access",
            "sub": str(user.pk),
            "username": user.username,
            "email": user.email,
            "groups": list(user.groups.values_list("name", flat=True)),
            "permissions": get_permissions_for_user(user),
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "iat": now,
            "exp": expires,
        }

        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    @staticmethod
    def create_refresh_token(user) -> str:
        """Create a refresh token for the user."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=settings.JWT_REFRESH_TOKEN_LIFETIME_DAYS)

        payload = {
            "type": "refresh",
            "sub": str(user.pk),
            "iat": now,
            "exp": expires,
        }

        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and validate a JWT token."""
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])

    @staticmethod
    def hash_token(token: str) -> str:
        """Create a SHA-256 hash of the token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()
