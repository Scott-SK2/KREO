from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AuthUserThrottle(UserRateThrottle):
    scope = "auth"


class AuthAnonThrottle(AnonRateThrottle):
    scope = "auth_ip"


class ApplicationsDailyThrottle(UserRateThrottle):
    """20 candidatures par jour et par compte en bêta."""

    scope = "applications_daily"

    def allow_request(self, request, view):
        if request.method != "POST":
            return True
        return super().allow_request(request, view)


class OpportunitiesDailyThrottle(UserRateThrottle):
    """5 annonces par jour et par compte en bêta."""

    scope = "opportunities_daily"

    def allow_request(self, request, view):
        if request.method != "POST":
            return True
        return super().allow_request(request, view)


class MessagesThrottle(UserRateThrottle):
    scope = "messages"

    def allow_request(self, request, view):
        if request.method != "POST":
            return True
        return super().allow_request(request, view)


class ReportsThrottle(UserRateThrottle):
    scope = "reports"
