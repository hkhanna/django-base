import getpass

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db import transaction
from allauth.socialaccount.models import SocialApp
from config.settings.local import env
import core.models
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
        confirm_password = getpass.getpass("Confirm password: ")
        if password != confirm_password:
            self.stderr.write("Passwords don't match.")
            exit(1)
        user = User.objects.create_superuser(email, password)

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

        # -- Sites -- #
        # Change initial site to localhost
        site = Site.objects.get(pk=1)
        site.name = "localhost"
        site.domain = "localhost:" + env("WEB_PORT")
        site.save()

        # -- Social Authentication Providers -- #
        # Google
        if env("SOCIAL_AUTH_GOOGLE_CLIENT_ID") and env("SOCIAL_AUTH_GOOGLE_SECRET_KEY"):
            google = SocialApp.objects.create(
                provider="google",
                name="Google",
                client_id=env("SOCIAL_AUTH_GOOGLE_CLIENT_ID"),
                secret=env("SOCIAL_AUTH_GOOGLE_SECRET_KEY"),
            )
            google.sites.add(site)

        # Github
        if env("SOCIAL_AUTH_GITHUB_CLIENT_ID") and env("SOCIAL_AUTH_GITHUB_SECRET_KEY"):
            github = SocialApp.objects.create(
                provider="github",
                name="Github",
                client_id=env("SOCIAL_AUTH_GITHUB_CLIENT_ID"),
                secret=env("SOCIAL_AUTH_GITHUB_SECRET_KEY"),
            )
            github.sites.add(site)
