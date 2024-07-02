from django.urls import path

from home import views

app_name = 'home'
urlpatterns = [

    path('', views.index, name='home'),
    # path('backup/', views.backup_view, name='backup'),
    # path('cleanup/', views.cleanup_view, name='cleanup'),
    # path('export/', views.export_view, name='export'),
    # path('cron_job/', views.cron_job_view, name='cron_job'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.signout, name='logout'),
    path('data/', views.data_view, name='data'),
    path('metadata/', views.metadata_view, name='metadata'),
    path('retrieve_metadata/', views.retrieve_metadata, name='retrieve_metadata'),
    path('collections/<str:dbname>', views.retrieve_collections, name='retrieve_collections'),
    path('add_collections/<str:dbname>', views.add_collections, name='add_collections'),
    path('retrieve_fields/<str:dbname>', views.retrieve_fields, name='retrieve_fields'),
    path('add_fields/<str:dbname>', views.add_fields, name='add_fields'),
    path('upload_csv_collections/<str:dbname>', views.upload_csv_collections, name='upload_csv_collections'), 
    path('upload_csv_fields/<str:dbname>', views.upload_csv_fields, name='upload_csv_fields'),
    path('export_collections_to_csv/<str:dbname>/', views.export_collections_to_csv, name='export_collections_to_csv'),
    path('export_fields_to_csv/<str:dbname>/', views.export_fields_to_csv, name='export_fields_to_csv'),
    path('settings/', views.settings_view, name='settings'),

]
