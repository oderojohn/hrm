import hashlib

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from django.utils import timezone

from apps.attendance.models import SyncAgent, SyncEvent


class SyncAgentAuthentication(BaseAuthentication):
    """Authenticates a local sync agent installation via a long-lived API key
    sent in the X-Api-Key header, instead of a JWT user login. On success,
    both request.user and request.auth are set to the SyncAgent instance.
    """

    def authenticate(self, request):
        raw_key = request.headers.get("X-Api-Key")
        if not raw_key:
            return None

        agent = SyncAgent.objects.filter(key_prefix=raw_key[:12], is_active=True).first()
        if not agent or agent.key_hash != hashlib.sha256(raw_key.encode()).hexdigest():
            # Logged even on failure — an admin should be able to see bad/expired
            # keys being used, not just successful pushes.
            SyncEvent.objects.create(
                agent=agent,
                event_type=SyncEvent.EventType.AUTH_FAILED,
                status=SyncEvent.Status.FAILED,
                summary="Rejected request with an invalid or inactive API key.",
                ip_address=request.META.get("REMOTE_ADDR"),
            )
            raise exceptions.AuthenticationFailed("Invalid API key.")

        agent.last_seen_at = timezone.now()
        agent.save(update_fields=["last_seen_at"])
        return (agent, agent)
