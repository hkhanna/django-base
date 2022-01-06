import logging
import threading
import uuid

from django.conf import settings

logger = logging.getLogger(__name__)
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


class SetRemoteAddrFromForwardedFor:
    """
    Middleware that sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, if the
    latter is set.
    This was adapted from a removed middleware in Django 1.1.
    See https://docs.djangoproject.com/en/2.1/releases/1.1/#removed-setremoteaddrfromforwardedfor-middleware
    It should be fine to use with Heroku since Heroku guarantees the last IP in the list is the
    originating IP address: https://stackoverflow.com/a/37061471
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            real_ip = request.META["HTTP_X_FORWARDED_FOR"]
        except KeyError:
            # This will happen in local development. We should just make sure
            # that we're not in prod.
            if settings.ENVIRONMENT == "production":
                logger.error("Heroku did not provide X-Forwarded-For header")
                request.META["REMOTE_ADDR"] = None
        else:
            # We use the last IP because it's the only reliable one since
            # its the one Heroku sets.
            # In theory the first one (element 0) should be the client IP,
            # but its not reliable since it can be spoofed.
            real_ip = real_ip.split(",")[-1].strip()
            request.META["REMOTE_ADDR"] = real_ip

        return self.get_response(request)
