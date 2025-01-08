from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
import core.services

User = get_user_model()


class Command(BaseCommand):
    help = "Seed local db for development purposes"

    @transaction.atomic
    def handle(self, *args, **options):
        # -- Users -- #
        email = "admin@localhost"
        password = "admin"
        user = core.services.user_create(
            email=email, password=password, is_staff=True, is_superuser=True
        )
        print(f"\n**--> Created superuser {email} with password {password} <--**\n")

        # -- Orgs -- #
        # Create an Org for the user with the user as the owner.
        plan = core.services.plan_create(name="Default Plan", is_default=True)
        core.services.org_create(
            name="Example Organization 1",
            domain="127.0.0.1:8020",
            owner=user,
            primary_plan=plan,
            default_plan=plan,
        )

        core.services.org_create(
            name="Example Organization 2",
            domain="127.0.0.1:8020",
            owner=user,
            primary_plan=plan,
            default_plan=plan,
        )

        # Note this org has a different domain than the other two.
        core.services.org_create(
            name="Example Organization 3",
            domain="localhost:8020",
            owner=user,
            primary_plan=plan,
            default_plan=plan,
        )
