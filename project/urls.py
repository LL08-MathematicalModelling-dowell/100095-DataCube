from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
    openapi.Info(
        title="Dowell Mongo API",
        default_version='version v1.0',
        description="Dowell Mongo API",
    ),
    public=True,
)

urlpatterns = [
    path('api/', include('dbdetails.urls')),
    path('', include('home.urls')),
    path('admin/', admin.site.urls),
    path('db_api/', include('api.urls')),

    path('api/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path('api/api.json/', schema_view.without_ui(cache_timeout=0), name='schema-swagger-ui'),
    # path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
