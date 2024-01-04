from django.urls import path
from .views import DataCrudView, GetDataView, CollectionView

urlpatterns = [
    path('crud/', DataCrudView.as_view(), name="crud"),
    path('get_data/', GetDataView.as_view(), name="get_data"),
    path('collections/', CollectionView.as_view(), name='add_collection'),
]
