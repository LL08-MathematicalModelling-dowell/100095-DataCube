from django.urls import path
from .views import DataCrudView, GetDataView, CollectionView, AddCollection
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('crud/', DataCrudView.as_view(), name="crud"),
    path('get_data/', GetDataView.as_view(), name="get_data"),
    path('collections/', CollectionView.as_view(), name='collections'),
    path('add_collection/', AddCollection.as_view(), name='add_collection'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)