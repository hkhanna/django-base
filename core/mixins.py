import typing
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect

from core import services, selectors


class OrgUserSettingPermissionMixin(UserPassesTestMixin):
    org_user_setting: typing.Optional[str] = None

    def test_func(self):
        if self.org_user_setting is None:
            raise ImproperlyConfigured(
                "%(cls)s is missing org_user_setting."
                % {"cls": self.__class__.__name__}
            )

        org_user = selectors.org_user_list(
            user=self.request.user, org=self.request.org
        ).get()

        # For now, we just return the truthiness of the setting but we can do value matching if it becomes necessary.
        return services.org_user_get_setting_value(
            org_user=org_user, slug=self.org_user_setting
        )


class OrgRequiredMixin(UserPassesTestMixin):
    """If the request does not have an org, redirect to a page that
    explains that a user needs an org to access the page."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not any(issubclass(base, LoginRequiredMixin) for base in cls.__mro__[1:]):
            raise TypeError(f"OrgRequiredMixin must be mixed with LoginRequiredMixin")

    def test_func(self):
        assert hasattr(self.request, "org"), "Did you forget to use the OrgMiddleware?"
        return self.request.org is not None

    def handle_no_permission(self):
        return redirect("org-required")
