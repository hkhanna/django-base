import pytest
from unittest.mock import Mock
from django.urls import reverse
import base.models.event
from ..models import Event


@pytest.fixture
def test_handler_setting(settings):
    settings.EVENT_HANDLERS["example_evt"] = "base.models.event.test_handler"
    yield
    del settings.EVENT_HANDLERS["example_evt"]


def test_event_emit(test_handler_setting, caplog, monkeypatch):
    """Emitting an event creates an Event, logs a message, and calls the handler."""
    mock = Mock()
    monkeypatch.setattr(base.models.event, "test_handler", mock, raising=False)

    event = Event.emit("example_evt", {"hello": "world"})
    assert Event.objects.count() == 1
    assert event.data == {"hello": "world"}
    assert str(event.id) in caplog.text
    assert mock.call_count == 1


def test_event_emit_default(monkeypatch):
    """Emitting an event without a handler calls the noop handler."""
    mock = Mock()
    monkeypatch.setattr(base.models.event, "noop", mock)
    Event.emit("example_evt", {"hello": "world"})
    assert mock.call_count == 1


def test_event_emit_view(client):
    """POST hook to emit event with good secret"""
    response = client.post(
        reverse("event_emit"),
        data={"type": "example_event", "hello": "world"},
        content_type="application/json",
        HTTP_X_EVENT_SECRET="test",
    )
    assert response.status_code == 201
    assert Event.objects.count() == 1
    event = Event.objects.first()
    assert event.type == "example_event"
    assert event.data == {"hello": "world"}


def test_event_emit_view_insecure(client):
    """POST hook to emit event without secret"""
    response = client.post(
        reverse("event_emit"),
        data={"type": "example_event", "hello": "world"},
        content_type="application/json",
    )

    assert response.status_code == 400
    assert Event.objects.count() == 0
