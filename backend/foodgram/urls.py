from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import CustomTokenLoginView, CustomTokenLogoutView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

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
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/auth/token/login/', CustomTokenLoginView.as_view(
    ), name='custom_token_login'),
    path('api/auth/token/logout/', CustomTokenLogoutView.as_view(
    ), name='custom_token_logout'),
    path('api/', include('api.urls')),
    path('api/', include('users.urls')),
    path('api/redoc/', schema_view.with_ui(
        'redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
