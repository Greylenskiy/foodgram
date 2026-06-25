from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from api.views import short_link_redirect

schema_view = get_schema_view(
    openapi.Info(
        title="Foodgram API",
        default_version='v1',
        description="Документация для API проекта Foodgram",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/redoc/', schema_view.with_ui(
        'redoc', cache_timeout=0), name='schema-redoc'),
    path('api/docs/', schema_view.with_ui(
        'swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('s/<int:recipe_id>/', short_link_redirect, name='short_link'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
