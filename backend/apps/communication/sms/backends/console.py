from apps.communication.sms.backends.base import BaseSMSBackend


class ConsoleSMSBackend(BaseSMSBackend):
    """Default SMS backend for development — logs to stdout instead of calling a real gateway."""

    def send(self, to, message):
        print(f"[SMS -> {to}]: {message}")
        return True
