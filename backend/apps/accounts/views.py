import base64
from io import BytesIO

import qrcode
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.accounts.serializers import UserSerializer
from apps.core.mixins import AuditLogMixin, ExportMixin
from apps.core.models import AuditLog, LoginHistory
from apps.core.permissions import IsSuperAdmin


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        password = request.data.get("password")
        otp_token = request.data.get("otp_token")
        ip = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        existing = User.objects.filter(email=email).first()
        user = authenticate(request, username=email, password=password)

        if user is None:
            if existing:
                LoginHistory.objects.create(
                    user=existing, ip_address=ip, user_agent=user_agent, success=False
                )
            return Response(
                {"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {"detail": "Account is disabled."}, status=status.HTTP_403_FORBIDDEN
            )

        if user.is_2fa_enabled:
            device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
            if not device or not otp_token or not device.verify_token(otp_token):
                return Response(
                    {"detail": "OTP required.", "requires_2fa": True},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        refresh = RefreshToken.for_user(user)
        LoginHistory.objects.create(
            user=user, ip_address=ip, user_agent=user_agent, success=True
        )
        AuditLog.objects.create(
            actor=user,
            action=AuditLog.Action.LOGIN,
            model_name="User",
            object_id=str(user.pk),
            object_repr=str(user),
            ip_address=ip,
        )

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )


class LogoutView(APIView):
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass
        AuditLog.objects.create(
            actor=request.user,
            action=AuditLog.Action.LOGOUT,
            model_name="User",
            object_id=str(request.user.pk),
            object_repr=str(request.user),
            ip_address=request.META.get("REMOTE_ADDR"),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not user.check_password(old_password):
            return Response(
                {"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            return Response({"detail": exc.messages}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])
        return Response({"detail": "Password updated."})


class TwoFactorSetupView(APIView):
    def post(self, request):
        user = request.user
        device, _ = TOTPDevice.objects.get_or_create(
            user=user, name="default", defaults={"confirmed": False}
        )
        if device.confirmed:
            return Response(
                {"detail": "2FA is already enabled."}, status=status.HTTP_400_BAD_REQUEST
            )

        qr_image = qrcode.make(device.config_url)
        buffer = BytesIO()
        qr_image.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response(
            {
                "qr_code": f"data:image/png;base64,{qr_base64}",
                "secret": device.config_url,
            }
        )


class TwoFactorVerifyView(APIView):
    def post(self, request):
        token = request.data.get("token")
        try:
            device = TOTPDevice.objects.get(user=request.user, name="default")
        except TOTPDevice.DoesNotExist:
            return Response(
                {"detail": "2FA has not been set up."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not device.verify_token(token):
            return Response(
                {"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST
            )

        device.confirmed = True
        device.save(update_fields=["confirmed"])
        request.user.is_2fa_enabled = True
        request.user.save(update_fields=["is_2fa_enabled"])
        return Response({"detail": "Two-factor authentication enabled."})


class TwoFactorDisableView(APIView):
    def post(self, request):
        TOTPDevice.objects.filter(user=request.user).delete()
        request.user.is_2fa_enabled = False
        request.user.save(update_fields=["is_2fa_enabled"])
        return Response({"detail": "Two-factor authentication disabled."})


class UserViewSet(AuditLogMixin, ExportMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsSuperAdmin]
    filterset_fields = ["role", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["date_joined", "email"]
    export_headers = ["Email", "First Name", "Last Name", "Role", "Active"]

    def export_row(self, obj):
        return [obj.email, obj.first_name, obj.last_name, obj.role, obj.is_active]
