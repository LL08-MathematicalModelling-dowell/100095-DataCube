import json
import pymongo
import datetime
import requests

from bson import ObjectId
from drf_yasg import openapi
from rest_framework import serializers

from bson.json_util import dumps
from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView
from dbdetails.script import MongoDatabases
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from dbdetails.cronjob_script import CronJobs
from drf_yasg.utils import swagger_auto_schema
from dateutil.relativedelta import relativedelta
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.status import HTTP_400_BAD_REQUEST


class GetDataBaseDetails(APIView):
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
        }
    ))
    def post(self, request):
        try:
            username = request.data.get("username", None)
            password = request.data.get("password", None)
            if not username or not password:
                return Response({"message": "Please provide login credentials", "success": False},
                                status=HTTP_400_BAD_REQUEST)
            if username != "jacob" and password != "jacob@123":
                return Response({"message": "Please provide Valid credentials", "success": False},
                                status=HTTP_400_BAD_REQUEST)

            ld_data = MongoDatabases()
            # databases = ld_data.get_all_databases()
            # print("All Databases list is : {}".format(databases))
            # for database in databases:
            #     collections = ld_data.get_all_database_collections(database)
            #     print("All Collections of Database \"{}\" are {}".format(database, collections))
            # for database in databases:
            #     doc_count = ld_data.get_documents_count_of_all_collections(database)
            #     print("All Collections documents of Database \"{}\" are {}".format(database, doc_count))
            res = ld_data.iterate_over_all_database()

            return Response(
                {"success": res['status'], "message": res['message']}, status=HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e), "success": False}, status=HTTP_400_BAD_REQUEST)


class LastUpdateTimeView(APIView):
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
        }
    ))
    def get(self, request):
        try:
            username = request.data.get("username", None)
            password = request.data.get("password", None)
            if not username or not password:
                return Response({"message": "Please provide login credentials", "success": False},
                                status=HTTP_400_BAD_REQUEST)
            if username != "jacob" and password != "jacob@123":
                return Response({"message": "Please provide Valid credentials", "success": False},
                                status=HTTP_400_BAD_REQUEST)

            db = MongoDatabases()
            data = db.get_last_update_of_all_collections()

            return Response(
                {"success": data['status'], "message": data['message']}, status=HTTP_200_OK)

        except Exception as e:
            return Response({"message": str(e), "success": False}, status=HTTP_400_BAD_REQUEST)


class GetLastInsertionTime(APIView):
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
        }
    ))
    def post(self, request):
        try:
            username = request.data.get("username", None)
            password = request.data.get("password", None)
            if not username or not password:
                return Response({"message": "Please provide login credentials", "success": False},
                                status=HTTP_400_BAD_REQUEST)
            if username != "jacob" and password != "jacob@123":
                return Response({"message": "Please provide Valid credentials", "success": False},
                                status=HTTP_400_BAD_REQUEST)

            ld_data = MongoDatabases()
            res = ld_data.get_last_insertion_time_of_all_collections()

            return Response(
                {"success": res['status'], "message": res['message']}, status=HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e), "success": False}, status=HTTP_400_BAD_REQUEST)


class GetDateDiff(APIView):
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
        }
    ))
    def post(self, request):
        try:
            username = request.data.get("username", None)
            password = request.data.get("password", None)
            if not username or not password:
                return Response({"message": "Please provide login credentials", "success": False},
                                status=HTTP_400_BAD_REQUEST)
            if username != "jacob" and password != "jacob@123":
                return Response({"message": "Please provide Valid credentials", "success": False},
                                status=HTTP_400_BAD_REQUEST)

            ld_data = MongoDatabases()
            res = ld_data.get_date_diff_of_all_collections()

            return Response(
                {"success": True, "data": res['data']}, status=HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e), "success": False}, status=HTTP_400_BAD_REQUEST)


class DeleteRecords(APIView):
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
        }
    ))
    def post(self, request):
        try:
            username = request.data.get("username", None)
            password = request.data.get("password", None)
            if not username or not password:
                return Response({"message": "Please provide login credentials", "success": False},
                                status=HTTP_400_BAD_REQUEST)

            if username != "jacob" or password != "jacob@123":
                return Response({"message": "Please provide valid credentials", "success": False},
                                status=HTTP_400_BAD_REQUEST)

            lld_data = MongoDatabases()
            time_diff_res = lld_data.get_date_diff_of_all_collections()
            if not time_diff_res['status']:
                return Response({"message": time_diff_res['message'], "success": False},
                                status=HTTP_400_BAD_REQUEST)

            curr_time = datetime.datetime.utcnow()
            for col_data in time_diff_res['data']:
                if int(col_data['date_diff']) >= 5:
                    deleted_res = lld_data.delete_records(col_data['database'], col_data['collection'], {
                        "last_insertion_time": {"$lt": curr_time - relativedelta(months=5)}})
                    if not deleted_res['status']:
                        return Response({"message": deleted_res['message'], "success": False},
                                        status=HTTP_400_BAD_REQUEST)

            return Response({"success": True, "message": "Records deleted successfully."}, status=HTTP_200_OK)

        except Exception as e:
            return Response({"message": str(e), "success": False}, status=HTTP_400_BAD_REQUEST)


class CreateBackup(APIView):
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
        }
    ))
    def post(self, request):
        try:
            username = request.data.get("username", None)
            password = request.data.get("password", None)
            if not username or not password:
                return Response({"message": "Please provide login credentials", "success": False},
                                status=HTTP_400_BAD_REQUEST)
            if username != "jacob" and password != "jacob@123":
                return Response({"message": "Please provide Valid credentials", "success": False},
                                status=HTTP_400_BAD_REQUEST)

            ld_data = MongoDatabases()
            res = ld_data.get_backup()

            return Response(
                {"success": True, "message": res['message']}, status=HTTP_200_OK)
        except Exception as e:
            return Response({"message": str(e), "success": False}, status=HTTP_400_BAD_REQUEST)


class Test(APIView):
    def get(self, request):
        return Response({"success": True, "message": "Service running"}, status=HTTP_200_OK)


@method_decorator(csrf_exempt, name='post')
class RestoreDB(APIView):
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
            'password': openapi.Schema(type=openapi.TYPE_STRING, description='string'),
        }
    ))
    def post(self, request):
        try:
            backup_date = request.data.get("backup_date", None)
            if not backup_date:
                return Response({"message": "Please provide valid backup date", "success": False},
                                status=HTTP_400_BAD_REQUEST)

            ld_data = MongoDatabases()
            res = ld_data.restore(backup_date)

            return Response(
                {"success": res["success"], "message": res["message"]}, status=res["status"])
        except Exception as e:
            return Response({"message": str(e), "success": False}, status=HTTP_400_BAD_REQUEST)


class BackupSerializer(serializers.Serializer):
    databases = serializers.ListField(child=serializers.CharField())
    collections = serializers.ListField(child=serializers.CharField())


class TakeBackupWithParams(APIView):
    def post(self, request, *args, **kwargs):
        serializer = BackupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        databases = data.get('databases', [])
        collections = data.get('collections', [])
        try:
            ld_data = MongoDatabases()
            res = ld_data.get_backup(databases=databases, collections=collections)
            return JsonResponse({'message': res['message']}, status=200, safe=False)

        except Exception:
            return JsonResponse({'message': 'Something went wrong!'}, status=404, safe=False)


class TakeBackup(APIView):
    def get(self, request):
        try:
            ld_data = MongoDatabases()
            res = ld_data.get_backup()
            return JsonResponse({'message': res['message']}, status=200, safe=False)

        except Exception:
            return JsonResponse({'message': 'Something went wrong!'}, status=404, safe=False)


@csrf_exempt
def get_collections(request):
    databases = request.POST.get('databases', [])
    mongodb = MongoDatabases()
    collections = mongodb.get_all_database_collections(databases)
    return JsonResponse({'collections': collections}, status=200, safe=False)


class GetCollections(APIView):
    def post(self, request, *args, **kwargs):
        databases = request.data.get('databases', [])
        url = "https://100014.pythonanywhere.com/api/userinfo/"
        session_id = request.session.get("session_id")
        if session_id:
            resp = requests.post(url, data={"session_id": session_id})
            user = json.loads(resp.text)
            cluster = settings.MONGODB_CLIENT
            db = cluster["datacube_metadata"]
            coll = db['metadata_collection']
            databases_from_db = coll.find({"userID": user.get("userinfo", {}).get("userID")}, {"database_name": 1})
            databasesDB = [x.get('database_name') for x in databases_from_db]

            collections = []
            data = {}
            for db_name in databasesDB:
                if db_name in databases:
                    colls = coll.find({"database_name": db_name})
                    if colls:
                        # Extract collection names from the cursor
                        collection_names = [doc["collection_names"] for doc in colls]
                        for collection_name_list in collection_names:
                            for collection_name_list_item in collection_name_list:
                                collections.append(collection_name_list_item)
                    data[db_name] = collections

            return JsonResponse({'collections': collections, 'collections_data': data}, status=HTTP_200_OK)
        else:
            return JsonResponse({'error': 'Session ID not found'}, status=HTTP_400_BAD_REQUEST)


@csrf_exempt
def restore_database(request):
    try:
        backup_date = request.POST.get("backup_date", None)
        if not backup_date:
            return Response({"message": "Please provide valid backup date", "success": False},
                            status=HTTP_400_BAD_REQUEST)

        ld_data = MongoDatabases()
        res = ld_data.restore(backup_date)

        return JsonResponse(
            {"success": res["success"], "message": res["message"]}, status=res["status"])

    except Exception:
        return JsonResponse({'message': 'Something went wrong!'}, status=404, safe=False)


@csrf_exempt
def delete_collection(request):
    try:
        database = request.POST.get("database", None)
        collection = request.POST.get("collection", None)
        if not database or not collection:
            return JsonResponse({"message": "Please provide valid database and collection name", "success": False},
                                status=HTTP_400_BAD_REQUEST, safe=False)

        ld_data = MongoDatabases()
        res = ld_data.delete_collection(database, collection)

        return JsonResponse(
            {"success": res["success"], "message": res["message"]}, status=res["status"])

    except Exception:
        return JsonResponse({'message': 'Something went wrong!'}, status=404, safe=False)


@csrf_exempt
def delete_database(request):
    try:
        database = request.POST.get("database", None)
        if not database:
            return Response({"message": "Please provide valid database and collection name", "success": False},
                            status=HTTP_400_BAD_REQUEST)

        ld_data = MongoDatabases()
        res = ld_data.delete_database(database)

        return JsonResponse(
            {"success": res["success"], "message": res["message"]}, status=res["status"])

    except Exception:
        return JsonResponse({'message': 'Something went wrong!'}, status=404, safe=False)


def authenticate_user(request):
    try:
        username = request.POST.get("username", None)
        password = request.POST.get("password", None)
        if not username or not password:
            return JsonResponse({"message": "Please provide username and password", "success": False},
                                status=HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if not user:
            return JsonResponse({'message': 'User not found!'}, status=HTTP_400_BAD_REQUEST, safe=False)
        return JsonResponse({"success": True, "message": "Login Successful!"}, status=HTTP_200_OK)
    except Exception:
        return JsonResponse({'message': 'Something went wrong!'}, status=HTTP_400_BAD_REQUEST, safe=False)


class AuthenticateUser(APIView):
    def post(self, request, *args, **kwargs):
        try:
            username = request.data.get("username", None)
            password = request.data.get("password", None)
            if not username or not password:
                return JsonResponse({"message": "Please provide username and password", "success": False},
                                    status=HTTP_400_BAD_REQUEST)

            user = authenticate(username=username, password=password)
            if not user:
                return JsonResponse({'message': 'User not found!'}, status=HTTP_400_BAD_REQUEST, safe=False)
            return JsonResponse({"success": True, "message": "Login Successful!"}, status=HTTP_200_OK)
        except Exception:
            return JsonResponse({'message': 'Something went wrong!'}, status=HTTP_400_BAD_REQUEST, safe=False)


class InitiateCron(APIView):
    def post(self, request, *args, **kwargs):
        try:
            time = request.data.get('time', None)
            cron_type = request.data.get('cron_type', None)
            function = request.GET.get('function', None)

            if function not in ['restore', 'backup']:
                return JsonResponse({
                    'success': False,
                    'message': 'Please provide function to be performed as param. Valid values are restore and backup'},
                    status=HTTP_400_BAD_REQUEST, safe=False)

            if not time:
                return JsonResponse({'success': False, 'message': 'Please provide time!'}, status=HTTP_400_BAD_REQUEST,
                                    safe=False)

            if cron_type not in ['daily', 'weekly', 'monthly', 'yearly']:
                return JsonResponse(
                    {
                        'success': False,
                        'message': 'Please provide cron_type. It should be daily, weekly, monthly, yearly'},
                    status=HTTP_400_BAD_REQUEST, safe=False)

            cronjob = CronJobs()
            cronjob.create_cronjob(time, cron_type, function)
            return JsonResponse({"success": True, "message": "Cronjob created Successfully!"}, status=HTTP_200_OK)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=HTTP_400_BAD_REQUEST, safe=False)


class LoadMongoCollection(APIView):
    def post(self, request, *args, **kwargs):
        try:
            database_name = request.data.get("db_name", "").strip()
            collection_name = request.data.get("collection", "").strip()
            page = int(request.data.get("page", 1))
            per_page = int(request.data.get("per_page", 5))
            sort = request.data.get("sort", "asc").strip()
            filter_query = request.data.get("filter", "").strip().replace("'", "\"")
            filter = json.loads(filter_query) if filter_query else {}

            if "_id" in filter:
                try:
                    filter["_id"] = ObjectId(filter["_id"])
                except Exception as e:
                    return JsonResponse({"message": f"Invalid filter _id: {str(e)}"}, status=400)

            if "id" in filter:
                try:
                    filter["_id"] = ObjectId(filter["id"])
                    del filter["id"]
                except Exception as e:
                    return JsonResponse({"message": f"Invalid filter id: {str(e)}"}, status=400)

            offset = (page - 1) * per_page
            client = settings.MONGODB_CLIENT
            database = client["datacube_" + database_name]

            if collection_name not in database.list_collection_names():
                return JsonResponse({"message": f"Collection '{collection_name}' does not exist in '{database_name}'"}, status=404)

            collection = database[collection_name]

            try:
                data_cursor = collection.find(filter).sort([("_id", pymongo.ASCENDING if sort == "asc" else pymongo.DESCENDING)])
                total_filtered_count = 0
                filtered_data = []

                for doc in data_cursor:
                    filtered_doc = {"_id": doc["_id"]}
                    keep_document = False

                    for key, value in doc.items():
                        if key.endswith("_operation"):
                            isDeleted = value.get('is_deleted', False)
                            related_key = key.replace('_operation', '')

                            if not isDeleted:
                                if related_key in doc:
                                    filtered_doc[related_key] = doc[related_key]
                                filtered_doc[key] = value
                                keep_document = True

                    if keep_document:
                        filtered_data.append(filtered_doc)
                        total_filtered_count += 1

                paginated_data = filtered_data[offset:offset + per_page]

                json_data = dumps(paginated_data)
                context = {"json_data": json_data, "page": page, "per_page": per_page, "total": total_filtered_count}
                return JsonResponse(context, status=200)

            except Exception as e:
                return JsonResponse({"message": f"Error retrieving data: {str(e)}"}, status=400)

        except ValueError as ve:
            return JsonResponse({"message": f"Value error: {str(ve)}"}, status=400)
        except Exception as ex:
            return JsonResponse({"message": "Something went wrong!"}, status=400)


class ExportCluster(APIView):
    def get(self, request):
        try:
            mongodb = MongoDatabases()
            return mongodb.export_cluster()
        except Exception as e:
            return Response({"message": str(e), "success": False}, status=HTTP_400_BAD_REQUEST)
