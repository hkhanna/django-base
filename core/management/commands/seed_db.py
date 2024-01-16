import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from config.settings.local import env
from core import services

User = get_user_model()


class Command(BaseCommand):
    help = "Seed local db for development purposes"

    @transaction.atomic
    def handle(self, *args, **options):
        # -- Users -- #
        # Create just one user for now that is a superuser
        email = input("Superuser email address: ")
        password = getpass.getpass()
        user = services.user_create(
            email=email, password=password, is_staff=True, is_superuser=True
        )

        # -- Orgs -- #
        # Create an additional Org for the user with the user as the owner.
        plan = services.plan_create(name="Other Plan")
        services.org_create(
            name="Example LLC",
            owner=user,
            is_personal=False,
            primary_plan=plan,
            default_plan=plan,
        )
