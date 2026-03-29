import json

import jwt
from django.contrib.auth import authenticate, get_user_model
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .services import JWTService

User = get_user_model()


@method_decorator(csrf_exempt, name="dispatch")
class LoginView(View):
    """Authenticate user and return JWT tokens."""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return JsonResponse(
                {"error": "Username and password are required"}, status=400
            )

        user = authenticate(request, username=username, password=password)

        if user is None:
            return JsonResponse({"error": "Invalid credentials"}, status=401)

        if not user.is_active:
            return JsonResponse({"error": "User account is disabled"}, status=401)

        access_token = JWTService.create_access_token(user)
        refresh_token = JWTService.create_refresh_token(user)

        return JsonResponse(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class RefreshView(View):
    """Refresh access token using refresh token."""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return JsonResponse({"error": "Refresh token is required"}, status=400)

        try:
            payload = JWTService.decode_token(refresh_token)
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Refresh token has expired"}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid refresh token"}, status=401)

        if payload.get("type") != "refresh":
            return JsonResponse({"error": "Invalid token type"}, status=401)

        try:
            user = User.objects.get(pk=payload["sub"])
        except User.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=401)

        if not user.is_active:
            return JsonResponse({"error": "User account is disabled"}, status=401)

        access_token = JWTService.create_access_token(user)

        return JsonResponse(
            {
                "access_token": access_token,
                "token_type": "Bearer",
            }
        )


class HealthView(View):
    """Health check endpoint."""

    def get(self, request):
        return JsonResponse({"status": "healthy"})
