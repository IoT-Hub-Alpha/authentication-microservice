import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

User = get_user_model()

# Groups to create (each microservice handles its own authorization)
GROUPS = ["Operators", "Viewers"]


class Command(BaseCommand):
    help = "Create admin superuser, groups, and users"

    def notify(self, message, status=None):
        """Write a styled message to stdout."""
        if status is None:
            self.stdout.write(message)
        else:
            style = getattr(self.style, status, self.style.SUCCESS)
            self.stdout.write(style(message))

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-superuser",
            action="store_true",
            help="Skip superuser creation",
        )
        parser.add_argument(
            "--skip-groups",
            action="store_true",
            help="Skip groups creation",
        )
        parser.add_argument(
            "--skip-users",
            action="store_true",
            help="Skip users creation",
        )

    def handle(self, *args, **options):
        if not options["skip_superuser"]:
            self.create_superuser()

        if not options["skip_groups"]:
            self.create_groups()

        if not options["skip_users"]:
            self.create_users()

        self.notify("\nSetup completed!", "SUCCESS")

    def create_superuser(self):
        """Create admin superuser."""
        self.notify("\nCreating superuser...")

        username = os.getenv("ADMIN_USERNAME", "admin")
        email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        password = os.getenv("ADMIN_PASSWORD", "admin123")

        if User.objects.filter(username=username).exists():
            self.notify(
                f'Superuser "{username}" already exists, skipping...', "WARNING"
            )
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.notify(f"Created superuser: {username}", "SUCCESS")
        self.notify(f"Email: {email}")

    def create_groups(self):
        """Create groups (authorization handled by each microservice)."""
        self.notify("\nCreating groups...")

        for group_name in GROUPS:
            group, created = Group.objects.get_or_create(name=group_name)

            if created:
                self.notify(f"Created group: {group_name}", "SUCCESS")
            else:
                self.notify(f'Group "{group_name}" already exists', "WARNING")

    def create_users(self):
        """Create operator and viewer users."""
        self.notify("\nCreating users...")

        users_config = [
            {
                "username": os.getenv("OPERATOR_USERNAME", "operator"),
                "email": os.getenv("OPERATOR_EMAIL", "operator@example.com"),
                "password": os.getenv("OPERATOR_PASSWORD", "operator123"),
                "group": "Operators",
            },
            {
                "username": os.getenv("VIEWER_USERNAME", "viewer"),
                "email": os.getenv("VIEWER_EMAIL", "viewer@example.com"),
                "password": os.getenv("VIEWER_PASSWORD", "viewer123"),
                "group": "Viewers",
            },
        ]

        for user_data in users_config:
            username = user_data["username"]
            group_name = user_data["group"]

            try:
                group = Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                self.notify(
                    f'Group "{group_name}" not found, skipping user "{username}"...',
                    "ERROR",
                )
                self.notify("Run without --skip-groups first", "WARNING")
                continue

            if User.objects.filter(username=username).exists():
                self.notify(f'User "{username}" already exists, skipping...', "WARNING")
                continue

            user = User.objects.create_user(
                username=username,
                email=user_data["email"],
                password=user_data["password"],
                is_staff=True,
            )
            user.groups.add(group)

            self.notify(f"Created user: {username}", "SUCCESS")
            self.notify(f"Email: {user_data['email']}")
            self.notify(f"Group: {group_name}")
