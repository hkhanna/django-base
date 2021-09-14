from .. import logging


def test_logger_name():
    """get_logger utility should be properly named"""
    logger = logging.get_logger(__name__)
    assert logger.name == "base-django.base.tests.test_logging"
