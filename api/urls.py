from django.urls import path
from .views import (
    DataCrudView, GetDataView,
    CollectionView, CreateDatabaseView,
    ListCollectionsView, AddCollectionView,
    )

app_name = 'db_api'

urlpatterns = [
    path('crud/', DataCrudView.as_view(), name="crud"),
    path('get_data/', GetDataView.as_view(), name="get_data"),
    path('collections/', CollectionView.as_view(), name='collections'),
    path('create_database/', CreateDatabaseView.as_view(), name='create_database'),
    path('list_collections/', ListCollectionsView.as_view(), name='list_collections'),
    path('add_collection/', CreateCollectionView.as_view(), name='add_collection'),
]
