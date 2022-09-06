import pytest
import json
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
    linked = factories.EmailMessageFactory(message_id="id-abc123")
    notlinked = factories.EmailMessageFactory(message_id="other-id")

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
    email_message = factories.EmailMessageFactory(message_id="id-abc123")
    payload = json.dumps(
        {
            "RecordType": record_type,
            "MessageID": email_message.message_id,
        }
    )
    client.post(url, payload, content_type="application/json")
    email_message.refresh_from_db()
    assert email_message.status == new_status
