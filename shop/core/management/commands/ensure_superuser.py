from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from config.env import env


class Command(BaseCommand):
    help = (
        "Create (or update the password of) a superuser from DJANGO_SUPERUSER_USERNAME / "
        "DJANGO_SUPERUSER_PASSWORD / DJANGO_SUPERUSER_EMAIL. Meant for automated deploys."
    )

    def handle(self, *args, **options) -> None:
        username = env.str("DJANGO_SUPERUSER_USERNAME", default="")
        password = env.str("DJANGO_SUPERUSER_PASSWORD", default="")
        email = env.str("DJANGO_SUPERUSER_EMAIL", default="admin@example.com")

        if not username or not password:
            self.stdout.write("DJANGO_SUPERUSER_USERNAME / DJANGO_SUPERUSER_PASSWORD are not set, skipping.")
            return

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )

        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = "created" if created else "updated"
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' {action}."))
