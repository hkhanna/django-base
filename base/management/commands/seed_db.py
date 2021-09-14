import getpass

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = "Seed local db for development purposes"

    @transaction.atomic
    def handle(self, *args, **options):
        # -- Users -- #
        # Create just one user for now that is a superuser
        email = input("Superuser email address: ")
        password = getpass.getpass()
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            self.stderr.write("Passwords don't match.")
            exit(1)
        user = User.objects.create_superuser(email, password)

        # -- Sites -- #
        # Change initial site to localhost
        site = Site.objects.get(pk=1)
        site.name = "localhost"
        site.domain = "localhost"
        site.save()