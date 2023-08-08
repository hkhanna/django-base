import typing
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured

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
        return services.org_user_get_setting(
            org_user=org_user, slug=self.org_user_setting
        )
