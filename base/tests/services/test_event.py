from unittest.mock import Mock

import pytest

from ... import services
from ...models import Event


@pytest.fixture(autouse=True)
def default_handler(settings):
    settings.EVENT_HANDLERS["default"] = "base.services.event_noop"


@pytest.fixture
def test_handler_setting(settings):
    settings.EVENT_HANDLERS["example_evt"] = "base.services.event_test_handler"
    yield
    del settings.EVENT_HANDLERS["example_evt"]


def test_event_emit(test_handler_setting, caplog, monkeypatch):
    """Emitting an event creates an Event, logs a message, and calls the handler."""
    mock = Mock()
    monkeypatch.setattr(services, "event_test_handler", mock, raising=False)

    event = services.event_emit(type="example_evt", data={"hello": "world"})
    assert Event.objects.count() == 1
    assert event.data == {"hello": "world"}
    assert str(event.id) in caplog.text
    assert mock.call_count == 1


def test_event_emit_default(monkeypatch):
    """Emitting an event without a handler calls the noop handler."""
    mock = Mock()
    monkeypatch.setattr(services, "event_noop", mock)
    services.event_emit(type="example_evt", data={"hello": "world"})
    assert mock.call_count == 1
