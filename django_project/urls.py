from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from security_channel.views import (
    metrics as quality_metrics,
    metrics_view,
    quality_dashboard,
)

urlpatterns = [
    path("", RedirectView.as_view(url="/security-channel/", permanent=False)),
    path("admin/", admin.site.urls),
    path("metrics/", quality_metrics, name="quality_metrics"),
    path("metrics-view/", metrics_view, name="quality_metrics_view"),
    path("quality-dashboard/", quality_dashboard, name="quality_dashboard"),
    path("security-channel/", include("security_channel.urls")),
]
