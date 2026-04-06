import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


@pytest.fixture
def operators_group(db):
    """Create Operators group."""
    group, _ = Group.objects.get_or_create(name="Operators")
    return group


@pytest.fixture
def viewers_group(db):
    """Create Viewers group."""
    group, _ = Group.objects.get_or_create(name="Viewers")
    return group


@pytest.fixture
def user(db):
    """Create a regular user without group."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def operator_user(db, operators_group):
    """Create user in Operators group."""
    user = User.objects.create_user(
        username="operator",
        email="operator@example.com",
        password="operator123",
        is_staff=True,
    )
    user.groups.add(operators_group)
    return user


@pytest.fixture
def viewer_user(db, viewers_group):
    """Create user in Viewers group."""
    user = User.objects.create_user(
        username="viewer",
        email="viewer@example.com",
        password="viewer123",
        is_staff=True,
    )
    user.groups.add(viewers_group)
    return user


@pytest.fixture
def superuser(db):
    """Create a superuser."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="admin123",
    )


@pytest.fixture
def inactive_user(db):
    """Create an inactive user."""
    return User.objects.create_user(
        username="inactive",
        email="inactive@example.com",
        password="inactive123",
        is_active=False,
    )
