import getpass

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.db import transaction
from config.settings.local import env

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
        site.domain = "localhost:" + env("WEB_PORT")
        site.save()

        # FIXME: To remove
        open_wh = {
            "RecordType": "Open",
            "MessageStream": "outbound",
            "FirstOpen": True,
            "Client": {
                "Name": "Chrome 35.0.1916.153",
                "Company": "Google",
                "Family": "Chrome",
            },
            "OS": {
                "Name": "OS X 10.7 Lion",
                "Company": "Apple Computer, Inc.",
                "Family": "OS X 10",
            },
            "Platform": "WebMail",
            "UserAgent": "Mozilla\/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit\/537.36 (KHTML, like Gecko) Chrome\/35.0.1916.153 Safari\/537.36",
            "Geo": {
                "CountryISOCode": "RS",
                "Country": "Serbia",
                "RegionISOCode": "VO",
                "Region": "Autonomna Pokrajina Vojvodina",
                "City": "Novi Sad",
                "Zip": "21000",
                "Coords": "45.2517,19.8369",
                "IP": "188.2.95.4",
            },
            "MessageID": "883953f4-6105-42a2-a16a-77a8eac79483",
            "Metadata": {"a_key": "a_value", "b_key": "b_value"},
            "ReceivedAt": "2019-11-05T16:33:54.9070259Z",
            "Tag": "welcome-email",
            "Recipient": "john@example.com",
        }

        bounce_wh = {
            "RecordType": "Bounce",
            "MessageStream": "outbound",
            "ID": 4323372036854775807,
            "Type": "HardBounce",
            "TypeCode": 1,
            "Name": "Hard bounce",
            "Tag": "Test",
            "MessageID": "883953f4-6105-42a2-a16a-77a8eac79483",
            "Metadata": {"a_key": "a_value", "b_key": "b_value"},
            "ServerID": 23,
            "Description": "The server was unable to deliver your message (ex: unknown user, mailbox not found).",
            "Details": "Test bounce details",
            "Email": "john@example.com",
            "From": "sender@example.com",
            "BouncedAt": "2019-11-05T16:33:54.9070259Z",
            "DumpAvailable": True,
            "Inactive": True,
            "CanActivate": True,
            "Subject": "Test subject",
            "Content": "<Full dump of bounce>",
        }

        delivery_wh = {
            "MessageID": "883953f4-6105-42a2-a16a-77a8eac79483",
            "Recipient": "john@example.com",
            "DeliveredAt": "2019-11-05T16:33:54.9070259Z",
            "Details": "Test delivery webhook details",
            "Tag": "welcome-email",
            "ServerID": 23,
            "Metadata": {"a_key": "a_value", "b_key": "b_value"},
            "RecordType": "Delivery",
            "MessageStream": "outbound",
        }

        spam = {
            "RecordType": "SpamComplaint",
            "MessageStream": "outbound",
            "ID": 42,
            "Type": "SpamComplaint",
            "TypeCode": 512,
            "Name": "Spam complaint",
            "Tag": "Test",
            "MessageID": "00000000-0000-0000-0000-000000000000",
            "Metadata": {"a_key": "a_value", "b_key": "b_value"},
            "ServerID": 1234,
            "Description": "",
            "Details": "Test spam complaint details",
            "Email": "john@example.com",
            "From": "sender@example.com",
            "BouncedAt": "2019-11-05T16:33:54.9070259Z",
            "DumpAvailable": True,
            "Inactive": True,
            "CanActivate": False,
            "Subject": "Test subject",
            "Content": "<Abuse report dump>",
        }
