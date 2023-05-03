from unittest.mock import Mock
import base.models.event
from ..models import Event


def test_event_emit(settings, caplog, monkeypatch):
    """Emitting an event creates an Event, logs a message, and calls the handler."""
    settings.EVENT_HANDLERS["example_evt"] = "base.models.event.test_handler"
    mock = Mock()
    monkeypatch.setattr(base.models.event, "test_handler", mock, raising=False)

    event = Event.emit("example_evt", {"hello": "world"})
    assert Event.objects.count() == 1
    assert str(event.id) in caplog.text
    assert mock.call_count == 1


def test_event_emit_default(monkeypatch):
    """Emitting an event without a handler calls the default handler."""
    mock = Mock()
    monkeypatch.setattr(base.models.event, "default_handler", mock)
    Event.emit("example_evt", {"hello": "world"})
    assert mock.call_count == 1
