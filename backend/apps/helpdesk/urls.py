from rest_framework.routers import DefaultRouter

from apps.helpdesk.views import TicketAttachmentViewSet, TicketCommentViewSet, TicketViewSet

router = DefaultRouter()
router.register("tickets", TicketViewSet, basename="ticket")
router.register("comments", TicketCommentViewSet, basename="ticket-comment")
router.register("attachments", TicketAttachmentViewSet, basename="ticket-attachment")

urlpatterns = router.urls
