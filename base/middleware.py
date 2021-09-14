from base import logging
import threading
import uuid

from django.conf import settings

logger = logging.get_logger(__name__)
local = threading.local()


# Inspired by https://github.com/dabapps/django-log-request-id/blob/284a264616c582f9d93263bd5d2be67b29996ca0/log_request_id/middleware.py
class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = self._get_request_id(request)
        request.id = request_id
        local.request_id = request_id

        response = self.get_response(request)

        # Don't log favicon
        if "favicon" not in request.path:
            # If an unhandled exception is raised in the view, this will never log.
            # But django.request will log at WARNING OR ERROR level, so it's okay.
            logger.info(self._get_log_message(request, response))

        if settings.REQUEST_ID_HEADER:
            response[settings.REQUEST_ID_HEADER] = request.id

        del local.request_id

        return response

    def _get_request_id(self, request):
        """If there is supposed to be a header, use that or 'none' if it's not present.
        Otherwise, generate our own request UUID."""
        request_id_header = settings.REQUEST_ID_HEADER
        if request_id_header:
            return request.headers.get(request_id_header, "none")
        else:
            return uuid.uuid4.hex()

    def _get_log_message(self, request, response):
        message = f"method={request.method} path={request.path} status={response.status_code} "
        user = getattr(request, "user", None)
        if user:
            message += f"User.id={user.id}"
        else:
            message += f"User.id=none"
        return message
