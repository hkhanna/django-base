import logging
import threading
import uuid
import pytz

from django.urls import resolve
from django.conf import settings
from django.utils import timezone

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
            self.log_request_id(request, response)

        if settings.REQUEST_ID_HEADER:
            response[settings.REQUEST_ID_HEADER] = request.id

        del local.request_id

        return response

    def log_request_id(self, request, response):
        msg = f"method={request.method} path={request.path} status={response.status_code} "
        user = getattr(request, "user", None)
        if user:
            msg += f"User.id={user.id}"
        else:
            msg += f"User.id=none"

        logger.info(msg)

    def _get_request_id(self, request):
        """If there is supposed to be a header, use that or 'none' if it's not present.
        Otherwise, generate our own request UUID."""
        request_id_header = settings.REQUEST_ID_HEADER
        if request_id_header:
            return request.headers.get(request_id_header, "none")
        else:
            return uuid.uuid4().hex


class SetRemoteAddrFromForwardedFor:
    """
    Middleware that sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, if the
    latter is set.
    This was adapted from a removed middleware in Django 1.1.
    See https://docs.djangoproject.com/en/2.1/releases/1.1/#removed-setremoteaddrfromforwardedfor-middleware
    It should be fine to use with Render since Render guarantees the first IP in the list is the
    originating IP address: https://feedback.render.com/features/p/send-the-correct-xforwardedfor
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
                request.META["REMOTE_ADDR"] = None

                # Render's health check doesn't provide this header but that's okay,
                # so don't log an error.
                if resolve(request.path_info).url_name != "health_check":
                    logger.error("Render did not provide X-Forwarded-For header")
        else:
            # We use the first IP in this list since in theory that should be
            # the client IP. And it appears that Render guarantees that it is
            # accurate.
            real_ip = real_ip.split(",")[0].strip()
            request.META["REMOTE_ADDR"] = real_ip

        return self.get_response(request)


class TimezoneMiddleware:
    """If the user has a timezone in their session, activate it."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz = None

        if request.user.is_authenticated:
            tz = request.session.get("detected_tz")

        if tz:
            timezone.activate(pytz.timezone(tz))
        else:
            timezone.deactivate()

        return self.get_response(request)
