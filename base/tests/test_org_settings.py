"""Tests related to settings for Orgs, OrgUsers, and Plans."""

# The general philosophy is this.
# There are 2 types of settings, settings for an Org (OrgSetting) and settings for an OrgUser (OUSetting).
# They are related to Orgs, OrgUsers and Plans in different ways.
# - OrgSettings are primarily related to a payment Plan. An Org may override an OrgSetting, in which case it will not look to the Plan for that OrgSetting.
# - If a Plan is queried for an OrgSetting, and that OrgSetting is not set on the Plan, it will materialize the setting on the Plan with the OrgSetting's default.
# - OUSettings should have defaults set by the Org. If an Org is accessed for an OUSetting default and it's not there, it will materialize it on the Org.
#    - At this point, it doesn't seem useful to attach OUSetting defaults to a Plan, so we don't. We can easily change this down the road though.
# - If a setting does not exist but is queried, that setting will autocreate with a value of 0.

# A one-time payment situation would probably only use the default Plan and override OrgSettings as the purchase is made.


"""Org.get_setting() in the normal case will retrieve the OrgSetting from the Plan"""

"""Org.get_setting() will prioritize any OrgSettingOverrides"""

"""Org.get_setting() will materialize an OrgSetting on the Plan if it isn't already on the Plan"""

"""Org.get_setting() will create an OrgSetting with a default of 0 if it is accessed but does not exist"""

"""If Org.current_period_end is expired, Org.get_setting() should look to Org.default_plan"""

"""If Org.current_period_end is None, the plan never expires."""

"""OrgUser.get_setting() where the OrgUser is the owner does... what?"""

"""OrgUser.get_setting() will first look to a direct setting on the OrgUser"""

"""OrgUser.get_setting() will look to Org defaults (materializing if necessary) if there is no direct setting on the OrgUser"""

"""OrgUser.get_setting() will create an OUSetting with a default of 0 if it is accessed but does not exist"""
