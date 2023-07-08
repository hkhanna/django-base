import typing
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured
from base.models import OrgUser


class OUSettingPermissionMixin(UserPassesTestMixin):
    ou_setting: typing.Optional[str] = None

    def test_func(self):
        if self.ou_setting is None:
            raise ImproperlyConfigured(
                "%(cls)s is missing ou_setting_slug." % {"cls": self.__class__.__name__}
            )

        ou = OrgUser.objects.get(user=self.request.user, org=self.request.org)

        # For now, we just return the truthiness of the setting but we can do value matching if it becomes necessary.
        return ou.get_setting(self.ou_setting)
