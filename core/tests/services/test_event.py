from unittest.mock import Mock

import pytest

from ... import services
from ...models import Event


@pytest.fixture(autouse=True)
def default_handler(settings):
    settings.EVENT_HANDLERS["default"] = "core.services.event_noop"


def test_event_emit(settings, caplog, monkeypatch):
    """Emitting an event creates an Event, logs a message, and calls the handler."""
    settings.EVENT_HANDLERS = {
        "default": "core.services.event_noop",
        "example_evt": "core.services.event_test_handler",
    }
    mock = Mock()
    monkeypatch.setattr(services, "event_test_handler", mock, raising=False)

    event = services.event_emit(type="example_evt", data={"hello": "world"})
    assert Event.objects.count() == 1
    assert event.data == {"hello": "world"}
    assert str(event.uuid) in caplog.text
    assert mock.call_count == 1


def test_event_emit_default(monkeypatch):
    """Emitting an event without a handler calls the noop handler."""
    mock = Mock()
    monkeypatch.setattr(services, "event_noop", mock)
    services.event_emit(type="example_evt", data={"hello": "world"})
    assert mock.call_count == 1


def test_event_subtype(settings, monkeypatch):
    """Emitting an event with a subtype calls the handler for that subtype,
    or if none, the parent type."""
    settings.EVENT_HANDLERS = {
        "default": "core.services.event_noop",
        "example_evt": "core.services.event_test_handler",
        "example_evt.x.y": "core.services.other_event_test_handler",
    }

    mock_parent = Mock()
    mock_sub = Mock()
    monkeypatch.setattr(services, "event_test_handler", mock_parent, raising=False)
    monkeypatch.setattr(services, "other_event_test_handler", mock_sub, raising=False)

    services.event_emit(type="example_evt.x.y.z", data={"hello": "world"})
    services.event_emit(type="example_evt.x.y", data={"hello": "world"})
    services.event_emit(type="example_evt.x", data={"hello": "world"})
    services.event_emit(type="example_evt", data={"hello": "world"})

    assert mock_sub.call_count == 2
    assert mock_parent.call_count == 2
