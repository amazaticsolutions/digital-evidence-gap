"""
URL Configuration for digital_evidence_gap project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    """Lightweight health check for the frontend to verify backend is up."""
    return JsonResponse({"status": "ok", "service": "digital-evidence-gap"})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health, name='health'),
    path('api/users/', include('src.users.urls')),
    path('api/evidence/', include('src.evidence.urls')),
    path('api/search/', include('src.search.urls')),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)