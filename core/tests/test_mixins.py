from .. import mixins, services, selectors, constants


def test_org_user_setting_permission_mixin(rf, user, org):
    """The OrgUserSettingPermissionMixin is a mixin that requires a given OrgUserSetting to be True."""
    org_user_setting = services.org_user_setting_create(
        type=constants.SettingType.BOOL,
        slug="test_setting",
        default="false",
        owner_value="true",
    )
    mixin = mixins.OrgUserSettingPermissionMixin()
    mixin.org_user_setting = "test_setting"
    request = rf.post("/test")
    request.user = user
    request.org = org
    mixin.request = request
    assert mixin.test_func() is False

    # Now, give the user the permission.
    org_user = selectors.org_user_list(org=org, user=user).get()
    _org_user_org_user_setting = services.org_user_org_user_setting_create(
        org_user=org_user, setting=org_user_setting, value="true"
    )
    assert mixin.test_func() is True
