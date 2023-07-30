import json
from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.urls import reverse_lazy
from django.utils import timezone
from freezegun import freeze_time
from waffle.testutils import override_switch

from .. import constants, factories, models, services
from ..models import Event

# -- EVENT SERVICES -- #


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


# -- EMAILMESSAGE SERVICES -- #


def test_send_email(user, mailoutbox, settings):
    """Create and send an EmailMessage"""
    service = services.EmailMessageService(
        created_by=user,
        subject="A subject",
        template_prefix="account/email/email_confirmation",
        to_name=user.name,
        to_email=user.email,
        template_context={
            "user_name": user.name,
            "user_email": user.email,
            "activate_url": "",
        },
    )

    service.email_message_send()
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.SENT
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "A subject"
    assert mailoutbox[0].to == [f"{user.name} <{user.email}>"]
    assert (
        mailoutbox[0].from_email
        == f"{settings.SITE_CONFIG['default_from_name']} <{settings.SITE_CONFIG['default_from_email']}>"
    )
    assert mailoutbox[0].reply_to == []


@pytest.mark.parametrize(
    "name,email,expected",
    [
        ("Bob Jones, Jr. ", "bob@example.com ", '"Bob Jones, Jr." <bob@example.com>'),
        (" ", " bob@example.com", "bob@example.com"),
    ],
)
def test_send_email_sanitize(user, name, email, expected, mailoutbox):
    """Sending an email properly sanitizes the addresses"""
    service = services.EmailMessageService(
        created_by=user,
        subject="A subject",
        template_prefix="account/email/email_confirmation",
        sender_name=name,
        sender_email=email,
        to_name=name,
        to_email=email,
        reply_to_name=name,
        reply_to_email=email,
        template_context={
            "user_name": name,
            "user_email": email,
            "activate_url": "",
        },
    )

    service.email_message_send()
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.SENT
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "A subject"
    assert mailoutbox[0].to == [expected]
    assert mailoutbox[0].from_email == expected
    assert mailoutbox[0].reply_to == [expected]


def test_subject_newlines(user, mailoutbox):
    """Subject newlines should be collapsed"""
    service = services.EmailMessageService(
        created_by=user,
        subject="""A subject
        
        Exciting!""",
        template_prefix="account/email/email_confirmation",
        to_name=user.name,
        to_email=user.email,
        template_context={
            "user_name": user.name,
            "user_email": user.email,
            "activate_url": "",
        },
    )

    service.email_message_send()
    service.email_message.refresh_from_db()
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "A subject Exciting!"


def test_subject_limit(user, mailoutbox, settings):
    """Truncate subject lines of more than 78 characters"""
    subject = factories.fake.pystr(min_chars=100, max_chars=100)
    expected = subject[: settings.MAX_SUBJECT_LENGTH - 3] + "..."
    service = services.EmailMessageService(
        created_by=user,
        subject=subject,
        template_prefix="account/email/email_confirmation",
        to_name=user.name,
        to_email=user.email,
        template_context={
            "user_name": user.name,
            "user_email": user.email,
            "activate_url": "",
        },
    )

    service.email_message_send()
    service.email_message.refresh_from_db()
    assert len(mailoutbox) == 1
    assert expected == mailoutbox[0].subject
    assert len(expected) == settings.MAX_SUBJECT_LENGTH


def test_email_attachment(user, mailoutbox):
    """Emails can have attachments"""
    service = services.EmailMessageService(
        created_by=user,
        subject="A subject",
        template_prefix="account/email/email_confirmation",
        to_name=user.name,
        to_email=user.email,
        template_context={
            "user_name": user.name,
            "user_email": user.email,
            "activate_url": "",
        },
    )
    attachments = [
        {
            "filename": "test.txt",
            "content": factories.fake.paragraph(),
            "mimetype": "text/plain",
        }
    ]

    service.email_message_send(attachments)
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.SENT
    assert len(mailoutbox) == 1
    assert len(mailoutbox[0].attachments) == 1


def test_email_attachment_from_instance_file_field(monkeypatch, user, mailoutbox):
    """Email can have attachments sourced from model instances (for binary files)"""
    # This is required for binary files since you can't put binary files
    # in a celery task message.
    m = Mock()
    m.read.return_value = b"12345"
    models.EmailMessage.file_field = ""
    monkeypatch.setattr(models.EmailMessage, "file_field", m)

    service = services.EmailMessageService(
        created_by=user,
        subject="A subject",
        template_prefix="account/email/email_confirmation",
        to_name=user.name,
        to_email=user.email,
        template_context={
            "user_name": user.name,
            "user_email": user.email,
            "activate_url": "",
        },
    )

    attachments = [
        {
            "filename": "test.pdf",
            "content_from_instance_file_field": {
                "app_label": "base",
                "model_name": "EmailMessage",
                "field_name": "file_field",
                "pk": service.email_message.pk,
            },
            "mimetype": "application/pdf",
        },
    ]

    service.email_message_send(attachments)
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.SENT
    assert len(mailoutbox) == 1
    assert len(mailoutbox[0].attachments) == 1
    assert mailoutbox[0].attachments[0][1] == b"12345"


def test_postmark_message_stream(user, mailoutbox):
    service = services.EmailMessageService(
        created_by=user,
        subject="A subject",
        template_prefix="account/email/email_confirmation",
        to_name=user.name,
        to_email=user.email,
        template_context={
            "user_name": user.name,
            "user_email": user.email,
            "activate_url": "",
        },
        postmark_message_stream="broadcast",
    )
    service.email_message_send()
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.SENT
    assert len(mailoutbox) == 1
    assert mailoutbox[0].message_stream == "broadcast"


def test_cooldown(user, mailoutbox):
    """A created_by/template_prefix/to_email combination has a cooldown period"""
    email_message_args = dict(
        created_by=user,
        subject="A subject",
        template_prefix="account/email/email_confirmation",
        to_name=user.name,
        to_email=user.email,
        template_context={
            "user_name": user.name,
            "user_email": user.email,
            "activate_url": "",
        },
    )

    # Send the first email
    service = services.EmailMessageService(**email_message_args)
    assert service.email_message_send() is True
    assert len(mailoutbox) == 1
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.SENT

    # Send an email with a different recipient
    service = services.EmailMessageService(
        **{**email_message_args, "to_email": "someone.else@example.com"}
    )
    assert service.email_message_send() is True
    assert len(mailoutbox) == 2
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.SENT

    # Cancel the third email that is identical to the first
    service = services.EmailMessageService(**email_message_args)
    assert service.email_message_send() is False
    assert len(mailoutbox) == 2
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.CANCELED

    # Send identical email if it is 181 seconds in the future
    with freeze_time(timezone.now() + timedelta(seconds=181)):
        service = services.EmailMessageService(**email_message_args)
        assert service.email_message_send() is True
        assert len(mailoutbox) == 3
        service.email_message.refresh_from_db()
        assert service.email_message.status == models.EmailMessage.Status.SENT


def test_cooldown_scopes(user, mailoutbox):
    """Email cancellation can be tightened by removing scopes"""
    email_message_args = dict(
        created_by=user,
        subject="A subject",
        template_prefix="account/email/email_confirmation",
        to_name=user.name,
        to_email=user.email,
        template_context={
            "user_name": user.name,
            "user_email": user.email,
            "activate_url": "",
        },
    )

    # Send the first email
    service = services.EmailMessageService(**email_message_args)
    assert service.email_message_send() is True
    assert len(mailoutbox) == 1
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.SENT

    # Email with different recipient cancels if "to" scope is removed
    service = services.EmailMessageService(
        **{**email_message_args, "to_email": "someone.else@example.com"}
    )
    assert service.email_message_send(scopes=["created_by", "template_prefix"]) is False
    assert len(mailoutbox) == 1
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.CANCELED

    # Email with different user cancels if "created_by" scope is removed
    service = services.EmailMessageService(
        **{**email_message_args, "created_by": factories.user_create()}
    )
    assert service.email_message_send(scopes=["template_prefix", "to"]) is False
    assert len(mailoutbox) == 1
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.CANCELED

    # Email with different template cancels if "template_prefix" scope is removed
    service = services.EmailMessageService(
        **{**email_message_args, "template_prefix": "account/email/password_reset_key"}
    )
    assert service.email_message_send(scopes=["created_by", "to"]) is False
    assert len(mailoutbox) == 1
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.CANCELED


@override_switch("disable_outbound_email", True)
def test_disable_outbound_email_waffle_switch(user, mailoutbox):
    """disable_outbound_email waffle switch should disable all outbound emails."""
    service = services.EmailMessageService(
        created_by=user,
        subject="A subject",
        template_prefix="account/email/email_confirmation",
        to_name=user.name,
        to_email=user.email,
        template_context={
            "user_name": user.name,
            "user_email": user.email,
            "activate_url": "",
        },
    )

    service.email_message_send()
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.ERROR
    assert (
        "disable_outbound_email waffle flag is True"
        in service.email_message.error_message
    )
    assert len(mailoutbox) == 0


def test_send_email_with_reply_to(user, mailoutbox, settings):
    """Create and send an EmailMessage with a reply to should work"""
    service = services.EmailMessageService(
        created_by=user,
        subject="A subject",
        template_prefix="account/email/email_confirmation",
        to_name=user.name,
        to_email=user.email,
        reply_to_name="Support",
        reply_to_email="support@example.com",
        template_context={
            "user_name": user.name,
            "user_email": user.email,
            "activate_url": "",
        },
    )

    service.email_message_send()
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.SENT
    assert len(mailoutbox) == 1
    assert mailoutbox[0].reply_to == ["Support <support@example.com>"]


def test_reply_to_name_no_email(user, mailoutbox, settings):
    """Blank reply_to_email with a non-blank reply_to_name raises an error"""
    service = services.EmailMessageService(
        created_by=user,
        subject="A subject",
        template_prefix="account/email/email_confirmation",
        to_name=user.name,
        to_email=user.email,
        reply_to_name="Reply to name",
        template_context={
            "user_name": user.name,
            "user_email": user.email,
            "activate_url": "",
        },
    )

    with pytest.raises(RuntimeError):
        service.email_message_send()
    service.email_message.refresh_from_db()
    assert service.email_message.status == models.EmailMessage.Status.ERROR
    assert len(mailoutbox) == 0


# -- EMAILMESSAGEWEBHOOK SERVICES -- #

emw_url = reverse_lazy("email_message_webhook")


@pytest.fixture
def emw_payload():
    return json.dumps(
        {
            "RecordType": "some_type",
            "MessageID": "id-abc123",
        }
    )


def test_receive_webhook(client, emw_payload):
    """A EmailMessageWebhook is received"""
    response = client.post(emw_url, emw_payload, content_type="application/json")
    assert response.status_code == 201
    webhook = models.EmailMessageWebhook.objects.all()
    assert len(webhook) == 1
    webhook = webhook[0]
    assert webhook.body == json.loads(emw_payload)
    assert webhook.status == models.EmailMessageWebhook.Status.PROCESSED


def test_bad_json(client):
    """Bad JSON isn't processed"""
    response = client.post(emw_url, "bad json", content_type="application/json")
    assert response.status_code == 400
    assert models.EmailMessageWebhook.objects.count() == 0


def test_type_recorded(client, emw_payload):
    """An EmailMessageWebhook records its type"""
    response = client.post(emw_url, emw_payload, content_type="application/json")
    assert response.status_code == 201
    assert models.EmailMessageWebhook.objects.count() == 1
    assert models.EmailMessageWebhook.objects.first().type == "some_type"


def test_email_message_linked(client, emw_payload):
    """An EmailMessageWebhook is linked to its related EmailMessage"""
    linked = factories.email_message_create(message_id="id-abc123")
    notlinked = factories.email_message_create(message_id="other-id")

    response = client.post(emw_url, emw_payload, content_type="application/json")
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
