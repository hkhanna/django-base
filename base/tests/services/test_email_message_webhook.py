import json
from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.urls import reverse_lazy
from django.utils import timezone

from ... import constants, factories, models, services
from ...exceptions import ApplicationError


@pytest.fixture
def headers():
    return {
        "X-Some-Header": "id-xyz456",
    }


def test_bad_json(headers):
    """Bad JSON isn't processed"""
    with pytest.raises(ApplicationError):
        services.email_message_webhook_create_from_request(
            body="bad json", headers=headers
        )

    assert models.EmailMessageWebhook.objects.count() == 0


# FIXME - move these somewhere else or change them once we have tasks use services

emw_url = reverse_lazy("email_message_webhook")


@pytest.fixture
def body():
    return json.dumps(
        {
            "RecordType": "some_type",
            "MessageID": "id-abc123",
        }
    )


def test_type_recorded(client, body):
    """An EmailMessageWebhook records its type"""
    response = client.post(emw_url, body, content_type="application/json")
    assert response.status_code == 201
    assert models.EmailMessageWebhook.objects.count() == 1
    assert models.EmailMessageWebhook.objects.first().type == "some_type"


def test_email_message_linked(client, body):
    """An EmailMessageWebhook is linked to its related EmailMessage"""
    linked = factories.email_message_create(message_id="id-abc123")
    notlinked = factories.email_message_create(message_id="other-id")

    response = client.post(emw_url, body, content_type="application/json")
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
    emw_payload = json.dumps(
        {
            "RecordType": record_type,
            "MessageID": email_message.message_id,
            ts_key: timezone.now().isoformat().replace("+00:00", "Z"),
        }
    )
    response = client.post(emw_url, emw_payload, content_type="application/json")
    assert response.status_code == 201
    email_message.refresh_from_db()
    assert email_message.status == new_status


def test_update_email_message_status_order(client):
    """An EmailMessageWebhook that arrives out of order should not regress the status."""
    email_message = factories.email_message_create(message_id="id-abc123")
    delivered_at = timezone.now()
    opened_at = delivered_at + timedelta(seconds=2)
    spam_at = opened_at + timedelta(seconds=5)

    emw_payload = json.dumps(
        {
            "RecordType": "Open",
            "MessageID": email_message.message_id,
            "ReceivedAt": opened_at.isoformat().replace("+00:00", "Z"),
        }
    )
    client.post(emw_url, emw_payload, content_type="application/json")

    emw_payload = json.dumps(
        {
            "RecordType": "Delivery",
            "MessageID": email_message.message_id,
            "DeliveredAt": delivered_at.isoformat().replace("+00:00", "Z"),
        }
    )
    client.post(emw_url, emw_payload, content_type="application/json")

    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.OPENED

    # IN-order webhook should still update
    emw_payload = json.dumps(
        {
            "RecordType": "SpamComplaint",
            "MessageID": email_message.message_id,
            "BouncedAt": spam_at.isoformat().replace("+00:00", "Z"),
        }
    )
    client.post(emw_url, emw_payload, content_type="application/json")

    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.SPAM
