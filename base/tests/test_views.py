import json
import pytest
from django.urls import reverse
from ..models import (
    Event,
    EmailMessageWebhook,
    OrgUser,
    OUSetting,
    OrgUserOUSetting,
    OrgInvitation,
)
from .assertions import assertMessageContains
from .. import factories, views, permissions, services, selectors, constants

# Generally, we prefer e2e tests with Playwright over view integration tests.
# However, when the view is something like a webhook endpoint, its easier
# to test it here.


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


def test_receive_webhook_view(client):
    """A EmailMessageWebhook is received and processed."""
    url = reverse("email_message_webhook")
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


def test_org_switch(client, user, org):
    """Switching an org simply sets request.org and persists that information to the session."""
    client.force_login(user)
    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org

    response = client.post(reverse("org_switch"), {"slug": user.personal_org.slug})
    assert response.wsgi_request.org == user.personal_org
    assert response.wsgi_request.session["org_slug"] == user.personal_org.slug


def test_org_switch_inactive(client, user, org):
    """A user may not switch to an inactive org"""
    personal = user.personal_org
    personal.is_active = False
    personal.full_clean()
    personal.save()

    client.force_login(user)
    response = client.get(reverse("index"))
    assert response.wsgi_request.org == org

    response = client.post(reverse("org_switch"), {"slug": personal.slug})
    assert response.status_code == 404
    assert response.wsgi_request.org == org
    assert response.wsgi_request.session["org_slug"] == org.slug


def test_org_switch_inactive_unauthorized(client, user):
    """A user may not switch to an org that they don't belong to."""
    org = factories.org_create()  # Different owner

    client.force_login(user)
    response = client.get(reverse("index"))
    assert response.wsgi_request.org == user.personal_org

    response = client.post(reverse("org_switch"), {"slug": org.slug})
    assert response.status_code == 404
    assert response.wsgi_request.org == user.personal_org
    assert response.wsgi_request.session["org_slug"] == user.personal_org.slug


def test_org_detail(client, user, org):
    """Org detail page shows members"""
    client.force_login(user)
    assert user.default_org == org
    other_user = factories.user_create()
    org.users.add(other_user)

    response = client.get(reverse("org_detail"))
    assert response.status_code == 200
    assert user.name in str(response.content)
    assert "Owner" in str(response.content)
    assert other_user.name in str(response.content)


def test_org_invitation_cancel(client, user):
    """Cancel an invitation"""
    client.force_login(user)
    email = factories.fake.email()
    client.post(reverse("org_invite"), {"email": email})
    assert OrgInvitation.objects.count() == 1
    uuid = OrgInvitation.objects.first().uuid
    response = client.post(reverse("org_invitation_cancel", kwargs={"uuid": uuid}))
    assertMessageContains(response, f"Invitation canceled.")
    assert OrgInvitation.objects.count() == 0


def test_ou_setting_permission_mixin(rf, user, org):
    """The OUSettingPermissionMixin is a mixin that requires a given OUSetting to be True."""
    org_user_setting = services.org_user_setting_create(
        type=constants.SettingType.BOOL, slug="test_setting", default=0, owner_value=1
    )
    mixin = views.OUSettingPermissionMixin()
    mixin.ou_setting = "test_setting"
    request = rf.post("/test")
    request.user = user
    request.org = org
    mixin.request = request
    assert mixin.test_func() is False

    # Now, give the user the permission.
    org_user = selectors.org_user_list(org=org, user=user).get()
    org_user_org_user_setting = services.org_user_org_user_setting_create(
        org_user=org_user, setting=org_user_setting, value=1
    )
    assert mixin.test_func() is True


def test_org_invitation_view_permissions():
    """The create, cancel, and resend invitation views require can_invite_members permission"""
    for view in (
        views.OrgInvitationCreateView,
        views.OrgInvitationCancelView,
        views.OrgInvitationResendView,
    ):
        assert views.LoginRequiredMixin in view.__bases__
        assert permissions.OUSettingPermissionMixin in view.__bases__
        assert view.ou_setting == "can_invite_members"


@pytest.mark.skip("Not implemented")
def test_invite_permission_ui(client, user, org):
    """Without can_invite_members permission, the UI doesn't show invitation, cancel, or resend button."""
    client.force_login(user)
    client.post(reverse("org_invite"), {"email": factories.fake.email()})
    response = client.get(reverse("org_detail"))
    assert "Invite a Member" in str(response.content)
    assert "Cancel Invitation" in str(response.content)
    assert "Resend Invitation" in str(response.content)

    ou = OrgUser.objects.get(user=user, org=org)
    setting = OUSetting.objects.get(slug="can_invite_members")
    OrgUserOUSetting.objects.create(
        org_user=ou, setting=setting, value=0
    )  # Remove can_invite_members from this OrgUser

    response = client.get(reverse("org_detail"))
    assert "Invite a Member" not in str(response.content)
    assert "Cancel Invitation" not in str(response.content)
    assert "Resend Invitation" not in str(response.content)
