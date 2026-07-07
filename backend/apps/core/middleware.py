import threading

_thread_locals = threading.local()


def get_current_request():
    return getattr(_thread_locals, "request", None)


def get_current_user():
    request = get_current_request()
    if request is not None and getattr(request, "user", None) and request.user.is_authenticated:
        return request.user
    return None


class AuditLogMiddleware:
    """Stashes the current request in a thread-local so model-layer code
    (signals, save() overrides) can attribute changes to a user without the
    caller having to thread `request` through every layer."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        try:
            response = self.get_response(request)
        finally:
            _thread_locals.request = None
        return response
