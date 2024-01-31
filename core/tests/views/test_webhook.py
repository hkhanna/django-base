import json
from django.urls import reverse

from ...models import (
    Event,
    EmailMessageWebhook,
)
from ... import constants


from ...models import Event


# Generally, we prefer e2e tests with playwright over view integration tests.
# However, when the view is something like a webhook endpoint, its easier
# to test it here.


def test_event_emit_view(client, settings):
    """POST hook to emit event with good secret"""
    settings.EVENT_HANDLERS["default"] = "core.services.event_noop"
    response = client.post(
        reverse("event_emit"),
        data={"type": "example_evt", "hello": "world"},
        content_type="application/json",
        HTTP_X_EVENT_SECRET="test",
    )
    assert response.status_code == 201
    assert Event.objects.count() == 1
    event = Event.objects.first()
    assert event.type == "example_evt"
    assert event.data == {"hello": "world"}


def test_event_emit_view_insecure(client):
    """POST hook to emit event without secret"""
    response = client.post(
        reverse("event_emit"),
        data={"type": "example_evt", "hello": "world"},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert Event.objects.count() == 0


def test_receive_webhook_view(client):
    """A EmailMessageWebhook is received and processed."""
    url = reverse("email-message-webhook")
    body = json.dumps(
        {
            "RecordType": "some_type",
            "MessageID": "id-abc123",
        }
    )

    response = client.post(url, body, content_type="application/json")
    assert response.status_code == 201
    webhook = EmailMessageWebhook.objects.all()
    assert len(webhook) == 1
    webhook = webhook[0]
    assert webhook.body == json.loads(body)
    assert webhook.status == constants.EmailMessageWebhook.Status.PROCESSED
