from rest_framework import serializers

from apps.recruitment.models import (
    Application,
    Candidate,
    Interview,
    JobVacancy,
    OfferLetter,
)


class JobVacancySerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )
    branch_name = serializers.CharField(source="branch.name", read_only=True, default=None)

    class Meta:
        model = JobVacancy
        fields = "__all__"


class CandidateSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Candidate
        fields = "__all__"


class ApplicationSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(source="candidate.full_name", read_only=True)
    vacancy_title = serializers.CharField(source="vacancy.title", read_only=True)

    class Meta:
        model = Application
        fields = "__all__"


class InterviewSerializer(serializers.ModelSerializer):
    interviewer_name = serializers.CharField(
        source="interviewer.full_name", read_only=True, default=None
    )

    class Meta:
        model = Interview
        fields = "__all__"


class OfferLetterSerializer(serializers.ModelSerializer):
    candidate_name = serializers.CharField(
        source="application.candidate.full_name", read_only=True, default=None
    )

    class Meta:
        model = OfferLetter
        fields = "__all__"
