import logging
import threading
import uuid

import pytz
from django.apps import apps
from django.conf import settings
from django.urls import resolve
from django.utils import timezone
from django.utils.cache import add_never_cache_headers

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
        if "favicon" not in request.path and "health_check" not in request.path:
            # If an unhandled exception is raised in the view, this will never log.
            # But django.request will log at WARNING OR ERROR level, so it's okay.
            self.log_request_id(request, response)

        if settings.REQUEST_ID_HEADER:
            response[settings.REQUEST_ID_HEADER] = request.id

        del local.request_id

        return response

    def log_request_id(self, request, response):
        msg = f"method={request.method} path={request.path} status={response.status_code} "
        ip = request.META["REMOTE_ADDR"]
        msg += f"ip={ip} "

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
    It should be fine to use with Heroku since Heroku guarantees the last IP in the list is the
    originating IP address: https://stackoverflow.com/a/37061471
    It should also be fine to use with Render since Render guarantees the first IP in the list is the
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
                    logger.error("X-Forwarded-For header not provided in prod.")
        else:
            if settings.RENDER:
                # We use the first IP in this list since in theory that should be
                # the client IP. And it appears that Render guarantees that it is
                # accurate.
                real_ip = real_ip.split(",")[0].strip()
                request.META["REMOTE_ADDR"] = real_ip
            elif settings.HEROKU:
                # We use the last IP because it's the only reliable one since
                # its the one Heroku sets.
                # In theory the first one (element 0) should be the client IP,
                # but its not reliable since it can be spoofed.
                real_ip = real_ip.split(",")[-1].strip()
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


class DisableClientCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        add_never_cache_headers(response)
        return response


class BadRouteDetectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if "accounts/social/" in request.path:
            logger.error(
                "A route in socialaccount was accessed that should not have been: "
                + request.path
            )
        response = self.get_response(request)
        return response


class HostUrlconfMiddleware:
    """ALT_URLCONF defines alternative urlconfs available based on an exact host match."""

    # N.B. If wildcard / subdomain matching becomes necessary to add, it should not be difficult.
    # I don't need it yet and can avoid a regex matching performance penalty on every request.
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        urlconf = settings.HOST_URLCONFS.get(request.get_host())
        if urlconf:
            request.urlconf = urlconf

        response = self.get_response(request)
        return response


class OrgMiddleware:
    """If there's no org in the session, set the org to the user's personal org, or if none, the most recently updated org."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        Org = apps.get_model("core", "Org")
        request.org = None

        # Only assign Orgs for authenticated users
        if request.user.is_authenticated:
            # If there's an org in the session and it's not invalid, use it.
            slug = request.session.get("org_slug")
            if slug:
                org = Org.objects.filter(
                    slug=slug, users=request.user, is_active=True
                ).first()
                if org:
                    request.org = org

            if request.org is None:
                # Otherwise, use the user's default org.
                request.org = request.user.default_org

        response = self.get_response(request)

        # If there's no longer a user (e.g., on logout or user delete),
        # remove the org.
        if not request.user.is_authenticated:
            request.org = None
            request.session["org_slug"] = None

        if request.org is not None:
            # Set it on the session
            request.session["org_slug"] = request.org.slug

            # Set the last accessed time
            ou = request.org.org_users.get(user=request.user)
            import core.services

            core.services.org_user_update(instance=ou, last_accessed_at=timezone.now())

        return response
