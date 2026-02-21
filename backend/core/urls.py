"""
URL Configuration for digital_evidence_gap project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Digital Evidence API",
        default_version='v1',
        description="""
## Digital Evidence Gap - Forensic Video Analysis API

This API provides endpoints for:
- **Evidence Management**: Upload, manage, and process video evidence
- **RAG Pipeline**: Process videos through the multimedia RAG engine
- **Search**: Query processed evidence with natural language
- **User Management**: Authentication and authorization

### Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```
        """,
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('src.users.urls')),
    path('api/evidence/', include('src.evidence.urls')),
    path('api/search/', include('src.search.urls')),
]

# Swagger/OpenAPI documentation URLs (development only)
if settings.DEBUG:
    urlpatterns += [
        re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
        path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
    ]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)