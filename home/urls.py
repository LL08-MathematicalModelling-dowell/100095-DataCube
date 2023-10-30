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
    path('settings/', views.settings_view, name='settings'),

]
