from django.urls import path

from .views import *


app_name = 'api'

urlpatterns = [
    path('database-details/', GetDataBaseDetails.as_view()),
    path('last-insertion-time/', GetLastInsertionTime.as_view()),
    path('get-date-difference/', GetDateDiff.as_view()),
    path('create-backup/', CreateBackup.as_view()),
    path('restore/', restore_database, name='restore'),
    path('delete_collection/', delete_collection, name='delete_collection'),
    path('delete_database/', delete_database, name='delete_database'),
    path('take-backup/', TakeBackup.as_view(), name='take-backup'),
    path('take-backup_with_params/', TakeBackupWithParams.as_view(), name='take-backup-with-params'),
    path('get-collections/', get_collections, name='get-collections'),
    path('authenticate-user/', AuthenticateUser.as_view(), name='authenticate_user'),
    path('load_mongo_collection/', LoadMongoCollection.as_view(), name='load_mongo_collections'),
    path('get-collection/', GetCollections.as_view(), name='get-collections'),
    path('initiate_cron/', InitiateCron.as_view(), name='initiate_cron'),
    path('export_cluster/', ExportCluster.as_view(), name='export_cluster'),

]
