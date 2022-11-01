"""Tests related to EmailMessages"""
import pytest
from unittest.mock import Mock
from datetime import timedelta
from waffle.testutils import override_switch
from django.utils import timezone
from freezegun import freeze_time
from .. import models, factories


def test_send_email(user, mailoutbox, settings):
    """Create and send an EmailMessage"""
    email_message = models.EmailMessage(
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

    settings.SITE_CONFIG[
        "default_reply_to_email"
    ] = None  # Override this in case an application sets it

    email_message.send()
    email_message.refresh_from_db()
    assert email_message.status == models.EmailMessage.Status.SENT
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "A subject"
    assert mailoutbox[0].to == [f"{user.name} <{user.email}>"]
    assert (
        mailoutbox[0].from_email
        == f"{settings.SITE_CONFIG['default_from_name']} <{settings.SITE_CONFIG['default_from_email']}>"
    )
    assert mailoutbox[0].reply_to == []


# FIXME:
"""Blank reply_to_email with a non-blank reply_to_name raises an error"""


@pytest.mark.parametrize(
    "name,email,expected",
    [
        ("Bob Jones, Jr. ", "bob@example.com ", '"Bob Jones, Jr." <bob@example.com>'),
        (" ", " bob@example.com", "bob@example.com"),
    ],
)
def test_send_email_sanitize(user, name, email, expected, mailoutbox):
    """Sending an email properly sanitizes the addresses"""
    # FIXME what happens if we dont sanitize subject?
    email_message = models.EmailMessage(
        created_by=user,
        subject="""A subject
        
        Exciting!""",
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

    email_message.send()
    email_message.refresh_from_db()
    assert email_message.status == models.EmailMessage.Status.SENT
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "A subject Exciting!"
    assert mailoutbox[0].to == [expected]
    assert mailoutbox[0].from_email == expected
    assert mailoutbox[0].reply_to == [expected]


def test_subject_limit(user, mailoutbox, settings):
    """Truncate subject lines of more than 78 characters"""
    # FIXME: test subject with newlines
    subject = factories.fake.pystr(min_chars=100, max_chars=100)
    expected = subject[: settings.MAX_SUBJECT_LENGTH - 3] + "..."
    email_message = models.EmailMessage(
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

    email_message.send()
    email_message.refresh_from_db()
    assert len(mailoutbox) == 1
    assert expected == mailoutbox[0].subject
    assert len(expected) == settings.MAX_SUBJECT_LENGTH


def test_email_attachment(user, mailoutbox):
    """Emails can have attachments"""
    email_message = models.EmailMessage(
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

    email_message.send(attachments)
    email_message.refresh_from_db()
    assert email_message.status == models.EmailMessage.Status.SENT
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

    email_message = models.EmailMessage(
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
    email_message.save()

    attachments = [
        {
            "filename": "test.pdf",
            "content_from_instance_file_field": {
                "app_label": "base",
                "model_name": "EmailMessage",
                "field_name": "file_field",
                "pk": email_message.pk,
            },
            "mimetype": "application/pdf",
        },
    ]

    email_message.send(attachments)
    email_message.refresh_from_db()
    assert email_message.status == models.EmailMessage.Status.SENT
    assert len(mailoutbox) == 1
    assert len(mailoutbox[0].attachments) == 1
    assert mailoutbox[0].attachments[0][1] == b"12345"


def test_postmark_message_stream(user, mailoutbox):
    email_message = models.EmailMessage(
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
    email_message.send()
    email_message.refresh_from_db()
    assert email_message.status == models.EmailMessage.Status.SENT
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
    email = models.EmailMessage.objects.create(**email_message_args)
    assert email.send() is True
    assert len(mailoutbox) == 1
    email.refresh_from_db()
    assert email.status == models.EmailMessage.Status.SENT

    # Send an email with a different recipient
    email = models.EmailMessage.objects.create(
        **{**email_message_args, "to_email": "someone.else@example.com"}
    )
    assert email.send() is True
    assert len(mailoutbox) == 2
    email.refresh_from_db()
    assert email.status == models.EmailMessage.Status.SENT

    # Cancel the third email that is identical to the first
    email = models.EmailMessage.objects.create(**email_message_args)
    assert email.send() is False
    assert len(mailoutbox) == 2
    email.refresh_from_db()
    assert email.status == models.EmailMessage.Status.CANCELED

    # Send identical email if it is 181 seconds in the future
    with freeze_time(timezone.now() + timedelta(seconds=181)):
        email = models.EmailMessage.objects.create(**email_message_args)
        assert email.send() is True
        assert len(mailoutbox) == 3
        email.refresh_from_db()
        assert email.status == models.EmailMessage.Status.SENT


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
    email = models.EmailMessage.objects.create(**email_message_args)
    assert email.send() is True
    assert len(mailoutbox) == 1
    email.refresh_from_db()
    assert email.status == models.EmailMessage.Status.SENT

    # Email with different recipient cancels if "to" scope is removed
    email = models.EmailMessage.objects.create(
        **{**email_message_args, "to_email": "someone.else@example.com"}
    )
    assert email.send(scopes=["created_by", "template_prefix"]) is False
    assert len(mailoutbox) == 1
    email.refresh_from_db()
    assert email.status == models.EmailMessage.Status.CANCELED

    # Email with different user cancels if "created_by" scope is removed
    email = models.EmailMessage.objects.create(
        **{**email_message_args, "created_by": factories.UserFactory()}
    )
    assert email.send(scopes=["template_prefix", "to"]) is False
    assert len(mailoutbox) == 1
    email.refresh_from_db()
    assert email.status == models.EmailMessage.Status.CANCELED

    # Email with different template cancels if "template_prefix" scope is removed
    email = models.EmailMessage.objects.create(
        **{**email_message_args, "template_prefix": "account/email/password_reset_key"}
    )
    assert email.send(scopes=["created_by", "to"]) is False
    assert len(mailoutbox) == 1
    email.refresh_from_db()
    assert email.status == models.EmailMessage.Status.CANCELED


@override_switch("disable_outbound_email", True)
def test_disable_outbound_email_waffle_switch(user, mailoutbox):
    """disable_outbound_email waffle switch should disable all outbound emails."""
    email_message = models.EmailMessage(
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

    email_message.send()
    email_message.refresh_from_db()
    assert email_message.status == models.EmailMessage.Status.ERROR
    assert "disable_outbound_email waffle flag is True" in email_message.error_message
    assert len(mailoutbox) == 0


def test_send_email_with_reply_to(user, mailoutbox, settings):
    """Create and send an EmailMessage with a default reply to should work"""
    settings.SITE_CONFIG["default_reply_to_name"] = "Support"
    settings.SITE_CONFIG["default_reply_to_email"] = "support@example.com"
    email_message = models.EmailMessage(
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

    email_message.send()
    email_message.refresh_from_db()
    assert email_message.status == models.EmailMessage.Status.SENT
    assert len(mailoutbox) == 1
    assert mailoutbox[0].reply_to == ["Support <support@example.com>"]
