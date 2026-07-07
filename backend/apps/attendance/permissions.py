from rest_framework.permissions import BasePermission

from apps.attendance.models import SyncAgent


class IsSyncAgent(BasePermission):
    """Grants access only to requests authenticated via SyncAgentAuthentication."""

    def has_permission(self, request, view):
        return isinstance(getattr(request, "auth", None), SyncAgent)
