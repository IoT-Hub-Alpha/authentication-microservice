from django.urls import include, path

from authentication.views import HealthView

urlpatterns = [
    path("v1/auth/", include("authentication.urls")),
    path("health", HealthView.as_view(), name="health"),
]
