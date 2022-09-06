import pytest
import json
from django.urls import reverse_lazy

from base import factories
from .. import models

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
    assert models.EmailMessageWebhook.objects.count() == 1
    assert models.EmailMessageWebhook.objects.first().body == json.loads(payload)


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
