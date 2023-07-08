import pytest
import json
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse_lazy

from base import factories
from .. import models, constants

url = reverse_lazy("email_message_webhook")


@pytest.fixture
def payload():
    return json.dumps(
        {
            "RecordType": "some_type",
            "MessageID": "id-abc123",
        }
    )


def test_receive_webhook(client, payload):
    """A EmailMessageWebhook is received"""
    response = client.post(url, payload, content_type="application/json")
    assert response.status_code == 201
    webhook = models.EmailMessageWebhook.objects.all()
    assert len(webhook) == 1
    webhook = webhook[0]
    assert webhook.body == json.loads(payload)
    assert webhook.status == models.EmailMessageWebhook.Status.PROCESSED


def test_bad_json(client):
    """Bad JSON isn't processed"""
    response = client.post(url, "bad json", content_type="application/json")
    assert response.status_code == 400
    assert models.EmailMessageWebhook.objects.count() == 0


def test_type_recorded(client, payload):
    """An EmailMessageWebhook records its type"""
    response = client.post(url, payload, content_type="application/json")
    assert response.status_code == 201
    assert models.EmailMessageWebhook.objects.count() == 1
    assert models.EmailMessageWebhook.objects.first().type == "some_type"


def test_email_message_linked(client, payload):
    """An EmailMessageWebhook is linked to its related EmailMessage"""
    linked = factories.email_message_create(message_id="id-abc123")
    notlinked = factories.email_message_create(message_id="other-id")

    response = client.post(url, payload, content_type="application/json")
    assert response.status_code == 201
    assert models.EmailMessageWebhook.objects.count() == 1
    assert models.EmailMessageWebhook.objects.first().email_message == linked


Status = constants.EmailMessage.Status


@pytest.mark.parametrize(
    "record_type,new_status",
    [
        ("Delivery", Status.DELIVERED),
        ("Open", Status.OPENED),
        ("Bounce", Status.BOUNCED),
        ("SpamComplaint", Status.SPAM),
    ],
)
def test_update_email_message_status(client, record_type, new_status):
    email_message = factories.email_message_create(message_id="id-abc123")
    ts_key = constants.WEBHOOK_TYPE_TO_TIMESTAMP[record_type]
    payload = json.dumps(
        {
            "RecordType": record_type,
            "MessageID": email_message.message_id,
            ts_key: timezone.now().isoformat().replace("+00:00", "Z"),
        }
    )
    response = client.post(url, payload, content_type="application/json")
    assert response.status_code == 201
    email_message.refresh_from_db()
    assert email_message.status == new_status


def test_update_email_message_status_order(client):
    """An EmailMessageWebhook that arrives out of order should not regress the status."""
    email_message = factories.email_message_create(message_id="id-abc123")
    delivered_at = timezone.now()
    opened_at = delivered_at + timedelta(seconds=2)
    spam_at = opened_at + timedelta(seconds=5)

    payload = json.dumps(
        {
            "RecordType": "Open",
            "MessageID": email_message.message_id,
            "ReceivedAt": opened_at.isoformat().replace("+00:00", "Z"),
        }
    )
    client.post(url, payload, content_type="application/json")

    payload = json.dumps(
        {
            "RecordType": "Delivery",
            "MessageID": email_message.message_id,
            "DeliveredAt": delivered_at.isoformat().replace("+00:00", "Z"),
        }
    )
    client.post(url, payload, content_type="application/json")

    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.OPENED

    # IN-order webhook should still update
    payload = json.dumps(
        {
            "RecordType": "SpamComplaint",
            "MessageID": email_message.message_id,
            "BouncedAt": spam_at.isoformat().replace("+00:00", "Z"),
        }
    )
    client.post(url, payload, content_type="application/json")

    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.SPAM
