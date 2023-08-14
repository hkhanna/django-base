import tempfile
from datetime import timedelta
from unittest.mock import Mock

import pytest
from django.utils import timezone
from freezegun import freeze_time

from .. import factories

from ... import constants, services


@pytest.fixture
def fp():
    fp = tempfile.TemporaryFile(mode="w+b")
    fp.write(factories.fake.binary())
    return fp


def test_send_email(user, mailoutbox, settings):
    """Create and send an EmailMessage"""
    email_message = services.email_message_create(
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

    services.email_message_queue(email_message=email_message)
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.SENT
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
    email_message = services.email_message_create(
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

    services.email_message_queue(email_message=email_message)
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.SENT
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "A subject"
    assert mailoutbox[0].to == [expected]
    assert mailoutbox[0].from_email == expected
    assert mailoutbox[0].reply_to == [expected]


def test_subject_newlines(user, mailoutbox):
    """Subject newlines should be collapsed"""
    email_message = services.email_message_create(
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

    services.email_message_queue(email_message=email_message)
    email_message.refresh_from_db()
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == "A subject Exciting!"


def test_subject_limit(user, mailoutbox, settings):
    """Truncate subject lines of more than 78 characters"""
    subject = factories.fake.pystr(min_chars=100, max_chars=100)
    expected = subject[: settings.MAX_SUBJECT_LENGTH - 3] + "..."
    email_message = services.email_message_create(
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

    services.email_message_queue(email_message=email_message)
    email_message.refresh_from_db()
    assert len(mailoutbox) == 1
    assert expected == mailoutbox[0].subject
    assert len(expected) == settings.MAX_SUBJECT_LENGTH


def test_email_attachment(user, mailoutbox, fp):
    """Emails can have attachments"""
    email_message = services.email_message_create(
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
    services.email_message_prepare(email_message=email_message)

    filename = factories.fake.file_name(extension="pdf")
    email_message_attachment = services.email_message_attach(
        email_message=email_message,
        fp=fp,
        filename=filename,
        mimetype="application/pdf",
    )

    services.email_message_queue(email_message=email_message)
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.SENT
    assert email_message.attachments.count() == 1
    assert len(mailoutbox) == 1
    assert len(mailoutbox[0].attachments) == 1
    assert (
        email_message_attachment.file.name
        == f"email_message_attachments/{email_message_attachment.uuid}.pdf"
    )
    assert mailoutbox[0].attachments[0][0] == filename
    fp.seek(0)
    assert mailoutbox[0].attachments[0][1] == fp.read()
    assert mailoutbox[0].attachments[0][2] == "application/pdf"


def test_postmark_message_stream(user, mailoutbox):
    email_message = services.email_message_create(
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
    services.email_message_queue(email_message=email_message)
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.SENT
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
    email_message = services.email_message_create(**email_message_args)
    assert services.email_message_queue(email_message=email_message) is True
    assert len(mailoutbox) == 1
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.SENT

    # Send an email with a different recipient
    email_message = services.email_message_create(
        **{**email_message_args, "to_email": "someone.else@example.com"}
    )
    assert services.email_message_queue(email_message=email_message) is True
    assert len(mailoutbox) == 2
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.SENT

    # Cancel the third email that is identical to the first
    email_message = services.email_message_create(**email_message_args)
    assert services.email_message_queue(email_message=email_message) is False
    assert len(mailoutbox) == 2
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.CANCELED

    # Send identical email if it is 181 seconds in the future
    with freeze_time(timezone.now() + timedelta(seconds=181)):
        email_message = services.email_message_create(**email_message_args)
        assert services.email_message_queue(email_message=email_message) is True
        assert len(mailoutbox) == 3
        email_message.refresh_from_db()
        assert email_message.status == constants.EmailMessage.Status.SENT


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
    email_message = services.email_message_create(**email_message_args)
    assert services.email_message_queue(email_message=email_message) is True
    assert len(mailoutbox) == 1
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.SENT

    # Email with different recipient cancels if "to" scope is removed
    email_message = services.email_message_create(
        **{**email_message_args, "to_email": "someone.else@example.com"}
    )
    assert (
        services.email_message_queue(
            email_message=email_message, scopes=["created_by", "template_prefix"]
        )
        is False
    )
    assert len(mailoutbox) == 1
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.CANCELED

    # Email with different user cancels if "created_by" scope is removed
    email_message = services.email_message_create(
        **{**email_message_args, "created_by": factories.user_create()}
    )
    assert (
        services.email_message_queue(
            email_message=email_message, scopes=["template_prefix", "to"]
        )
        is False
    )
    assert len(mailoutbox) == 1
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.CANCELED

    # Email with different template cancels if "template_prefix" scope is removed
    email_message = services.email_message_create(
        **{**email_message_args, "template_prefix": "account/email/password_reset_key"}
    )
    assert (
        services.email_message_queue(
            email_message=email_message, scopes=["created_by", "to"]
        )
        is False
    )
    assert len(mailoutbox) == 1
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.CANCELED


def test_disable_outbound_email_global_setting(user, mailoutbox):
    """disable_outbound_email GlobalSetting should disable all outbound emails."""
    services.global_setting_create(
        slug="disable_outbound_email", type=constants.SettingType.BOOL, value=1
    )
    email_message = services.email_message_create(
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

    services.email_message_queue(email_message=email_message)
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.ERROR
    assert "GlobalSetting disable_outbound_email is True" in email_message.error_message
    assert len(mailoutbox) == 0


def test_send_email_with_reply_to(user, mailoutbox, settings):
    """Create and send an EmailMessage with a reply to should work"""
    email_message = services.email_message_create(
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

    services.email_message_queue(email_message=email_message)
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.SENT
    assert len(mailoutbox) == 1
    assert mailoutbox[0].reply_to == ["Support <support@example.com>"]


def test_reply_to_name_no_email(user, mailoutbox, settings):
    """Blank reply_to_email with a non-blank reply_to_name raises an error"""
    email_message = services.email_message_create(
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
        services.email_message_queue(email_message=email_message)
    email_message.refresh_from_db()
    assert email_message.status == constants.EmailMessage.Status.ERROR
    assert len(mailoutbox) == 0
