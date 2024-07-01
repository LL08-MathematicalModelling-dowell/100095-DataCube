from django.urls import path
from .views import DataCrudView, GetDataView, CollectionView, AddCollection, AddDatabase, serviceInfo

urlpatterns = [
    path('crud/', DataCrudView.as_view(), name="crud"),
    path('get_data/', GetDataView.as_view(), name="get_data"),
    path('collections/', CollectionView.as_view(), name='collections'),
    # path('add_collection/', AddCollection.as_view(), name='add_collection'),
    # path('add_database/', AddDatabase.as_view(), name='add_database'),
    path('health_check/', serviceInfo.as_view())
]
