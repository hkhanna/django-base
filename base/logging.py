import logging


def get_logger(name):
    """Return a logger named appropriately"""
    return logging.getLogger("base-django." + name)
