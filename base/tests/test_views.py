from django.urls import reverse
from ..models import Event


def test_event_emit_view(client):
    """POST hook to emit event with good secret"""
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
