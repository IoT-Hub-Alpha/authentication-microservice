import jwt
import pytest
from django.conf import settings

from authentication.services import (
    JWTService,
    get_permissions_for_user,
    load_role_permissions,
)


class TestLoadRolePermissions:
    def test_loads_permissions_from_json(self):
        permissions = load_role_permissions()

        assert "Operators" in permissions
        assert "Viewers" in permissions
        assert "devices.view" in permissions["Operators"]
        assert "devices.view" in permissions["Viewers"]

    def test_operators_have_more_permissions_than_viewers(self):
        permissions = load_role_permissions()

        assert len(permissions["Operators"]) > len(permissions["Viewers"])

    def test_operators_can_add_devices(self):
        permissions = load_role_permissions()

        assert "devices.add" in permissions["Operators"]
        assert "devices.add" not in permissions["Viewers"]


class TestGetPermissionsForUser:
    def test_operator_gets_operator_permissions(self, operator_user):
        permissions = get_permissions_for_user(operator_user)

        assert "devices.view" in permissions
        assert "devices.add" in permissions
        assert "devices.change" in permissions

    def test_viewer_gets_viewer_permissions(self, viewer_user):
        permissions = get_permissions_for_user(viewer_user)

        assert "devices.view" in permissions
        assert "devices.add" not in permissions
        assert "devices.change" not in permissions

    def test_superuser_gets_all_permissions(self, superuser):
        permissions = get_permissions_for_user(superuser)
        role_permissions = load_role_permissions()

        # Should have all permissions from all roles
        all_perms = set()
        for perms in role_permissions.values():
            all_perms.update(perms)

        for perm in all_perms:
            assert perm in permissions

    def test_user_without_group_gets_no_permissions(self, user):
        permissions = get_permissions_for_user(user)

        assert permissions == []

    def test_permissions_are_sorted(self, operator_user):
        permissions = get_permissions_for_user(operator_user)

        assert permissions == sorted(permissions)


class TestJWTService:
    def test_create_access_token(self, operator_user):
        token = JWTService.create_access_token(operator_user)

        assert token is not None
        assert isinstance(token, str)

    def test_access_token_contains_required_fields(self, operator_user):
        token = JWTService.create_access_token(operator_user)
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])

        assert payload["type"] == "access"
        assert payload["sub"] == str(operator_user.pk)
        assert payload["username"] == operator_user.username
        assert payload["email"] == operator_user.email
        assert "groups" in payload
        assert "permissions" in payload
        assert "is_staff" in payload
        assert "is_superuser" in payload
        assert "iat" in payload
        assert "exp" in payload

    def test_access_token_includes_groups(self, operator_user):
        token = JWTService.create_access_token(operator_user)
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])

        assert "Operators" in payload["groups"]

    def test_access_token_includes_permissions(self, operator_user):
        token = JWTService.create_access_token(operator_user)
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])

        assert "devices.view" in payload["permissions"]

    def test_create_refresh_token(self, operator_user):
        token = JWTService.create_refresh_token(operator_user)

        assert token is not None
        assert isinstance(token, str)

    def test_refresh_token_contains_required_fields(self, operator_user):
        token = JWTService.create_refresh_token(operator_user)
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])

        assert payload["type"] == "refresh"
        assert payload["sub"] == str(operator_user.pk)
        assert "iat" in payload
        assert "exp" in payload

    def test_refresh_token_does_not_contain_permissions(self, operator_user):
        token = JWTService.create_refresh_token(operator_user)
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])

        assert "permissions" not in payload
        assert "groups" not in payload

    def test_decode_token(self, operator_user):
        token = JWTService.create_access_token(operator_user)
        payload = JWTService.decode_token(token)

        assert payload["username"] == operator_user.username

    def test_decode_invalid_token_raises(self):
        with pytest.raises(jwt.InvalidTokenError):
            JWTService.decode_token("invalid.token.here")

    def test_hash_token(self):
        token = "test_token_123"
        hash1 = JWTService.hash_token(token)
        hash2 = JWTService.hash_token(token)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars
        assert hash1 != token
