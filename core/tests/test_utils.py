from .. import utils


def test_get_display_name_no_name(user):
    """User without name can still get a branded email"""
    user.first_name = ""
    user.last_name = ""
    user.display_name = ""
    expected = f"{user.email} via Magistrate"
    actual = utils.get_email_display_name(
        user, "From", "example@example.com", "via Magistrate"
    )
    assert expected == actual


def test_get_display_name_no_name_long_email(user):
    """User without name and a long email can still get a branded email"""
    user.first_name = ""
    user.last_name = ""
    user.display_name = ""
    user.email = "a" * 80 + "b@example.com"
    available = 78 - len(" via Magistrate <example@example.com>") - len("From: ")
    expected = "a" * available + " via Magistrate"
    actual = utils.get_email_display_name(
        user, "From", "example@example.com", "via Magistrate"
    )
    assert expected == actual
