from rest_framework.routers import DefaultRouter

from apps.recruitment.views import (
    ApplicationViewSet,
    CandidateViewSet,
    InterviewViewSet,
    JobVacancyViewSet,
    OfferLetterViewSet,
)

router = DefaultRouter()
router.register("job-vacancies", JobVacancyViewSet, basename="job-vacancy")
router.register("candidates", CandidateViewSet, basename="candidate")
router.register("applications", ApplicationViewSet, basename="application")
router.register("interviews", InterviewViewSet, basename="interview")
router.register("offer-letters", OfferLetterViewSet, basename="offer-letter")

urlpatterns = router.urls
