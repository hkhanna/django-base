import json
from django.test.client import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from ...tests import factories

User = get_user_model()


class Command(BaseCommand):
    help = "Seed local db with Postmark webhooks and EmailMessages (for testing)"

    def handle(self, *args, **options):
        # -- EmailMessage -- #
        try:
            factories.email_message_create(
                template_prefix="email/base",
                to_email="harry@example.com",
                template_context={"some": "context"},
                message_id="883953f4-6105-42a2-a16a-77a8eac79483",
            )
        except IntegrityError:
            pass

        # -- EmailMessageWebhooks -- #

        # These examples were lifted directly off the Postmark Documentation
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

        spam_wh = {
            "RecordType": "SpamComplaint",
            "MessageStream": "outbound",
            "ID": 42,
            "Type": "SpamComplaint",
            "TypeCode": 512,
            "Name": "Spam complaint",
            "Tag": "Test",
            "MessageID": "883953f4-6105-42a2-a16a-77a8eac79483",
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

        for wh in (delivery_wh, open_wh, bounce_wh, spam_wh):
            url = reverse("email_message_webhook")
            Client(SERVER_NAME="localhost").post(
                url, json.dumps(wh), content_type="application/json"
            )
