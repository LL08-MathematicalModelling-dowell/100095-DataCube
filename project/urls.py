from drf_yasg import openapi

from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view


schema_view = get_schema_view(
    openapi.Info(
        title="Dowell Mongo API",
        default_version='version v1.0',
        description="Dowell Mongo API",
    ),
    public=True,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
