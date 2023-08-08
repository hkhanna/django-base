import logging
from core.middleware import local


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(local, "request_id", "none")
        return True
