import traceback
import pymongo
from bson import ObjectId
from django.core.exceptions import ValidationError
import requests
from rest_framework import status
from rest_framework.views import APIView
from pathlib import Path
from django.conf import settings

from dbdetails.script import MongoDatabases, dowell_time
from .serializers import *
import json
from rest_framework.response import Response
from .helpers import check_api_key, measure_execution_time
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import re
import time
from pymongo import MongoClient
from datetime import datetime
from rest_framework.exceptions import ValidationError

@method_decorator(csrf_exempt, name='dispatch')
class serviceInfo(APIView):
    def get(self, request):
        return Response({
            "success": True,
            "message": "Welcome to our API service."
        }, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class DataCrudView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            serializer = InputGetSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            database = data.get('db_name')
            coll = data.get('coll_name')
            operation = data.get('operation')
            api_key = data.get('api_key')
            filters = serializer.validated_data.get('filters', {})
            limit = int(data.get('limit')) if 'limit' in data else None
            offset = int(data.get('offset')) if 'offset' in data else None
            payment = data.get('payment', True)
            for key, value in filters.items():
                if key in ["id", "_id"]:
                    try:
                        filters[key] = ObjectId(value)
                    except Exception as ex:
                        print(ex)
                        pass

            cluster = settings.MONGODB_CLIENT
            # start_time = time.time()
            mongoDb = settings.METADATA_COLLECTION.find_one({"database_name": database})
            # end_time = time.time()
            # print(f"fetch operation took: {measure_execution_time(start_time, end_time)} seconds", "find one collection from db:")

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            # start_time = time.time()
            mongodb_coll = settings.METADATA_COLLECTION.find_one({"collection_names": {"$in": [coll]}})
            # end_time = time.time()
            # print(f"fetch operation mongodb_coll took: {measure_execution_time(start_time, end_time)} seconds", "mongodb_coll from db:")

            if not mongodb_coll:
                return Response(
                    {"success": False, "message": f"Collection '{coll}' does not exist in Datacube database",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            new_db = cluster["datacube_" + database]
            new_collection = new_db[coll]

            if operation not in ["fetch"]:
                return Response({"success": False, "message": "Operation not allowed", "data": []},
                                status=status.HTTP_405_METHOD_NOT_ALLOWED)
            if payment:
                res = check_api_key(api_key)

                if res != "success":
                    return Response(
                        {"success": False, "message": res,
                         "data": []},
                        status=status.HTTP_404_NOT_FOUND)

            result = None
            if operation == "fetch":
                query = new_collection.find(filters)
                if offset is not None:
                    query = query.skip(offset)
                if limit is not None:
                    query = query.limit(limit)
                result = query
            result = list(result)
            for doc in result:
                doc['_id'] = str(doc['_id'])
            if len(result) > 0:
                msg = "Data found!"
            else:
                msg = "No data exists for this query/collection"

            return Response({"success": True, "message": msg, "data": result}, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response({"success": False, "message": str(e), "data": []},
                            status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        try:
            serializer = InputPostSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            database = data.get('db_name')
            coll = data.get('coll_name')
            operation = data.get('operation')
            data_type = data.get('data_type')
            data_to_insert = data.get('data', {})
            api_key = data.get('api_key')
            payment = data.get('payment', True)

            cluster = settings.MONGODB_CLIENT
            mongo_db = settings.METADATA_COLLECTION.find_one({"database_name": database})

            if not mongo_db:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                    "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            mongodb_coll = settings.METADATA_COLLECTION.find_one({"database_name": database, "collection_names": {"$in": [coll]}})

            if not mongodb_coll:
                return Response(
                    {"success": False, "message": f"Collection '{coll}' does not exist in Datacube database",
                    "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            if operation not in ["insert"]:
                return Response({"success": False, "message": "Operation not allowed", "data": []},
                                status=status.HTTP_405_METHOD_NOT_ALLOWED)
                
            if data_type not in serializer.choose_data_type:
                return Response({"success": False, "message": "Data type not allowed", "data": []},
                                status=status.HTTP_405_METHOD_NOT_ALLOWED)

            if payment:
                res = check_api_key(api_key)

                if res != "success":
                    return Response(
                        {"success": False, "message": res,
                        "data": []},
                        status=status.HTTP_404_NOT_FOUND)

            if operation == "insert":

                new_db = cluster["datacube_" + database]
                new_collection = new_db[coll]

                existing_document_count = new_collection.count_documents({})

                if existing_document_count + 1 > 10000:
                    return Response(
                        {"success": False, "message": f"10,000 number of documents reached in '{coll}' collection",
                        "data": []},
                        status=status.HTTP_400_BAD_REQUEST)
                    
                for key, value in data_to_insert.items():
                    if key not in mongodb_coll['field_labels']:
                        return Response(
                        {"success": False, "message": f"New added field '{key}' is not registered in metadata collection",
                        "data": []},
                        status=status.HTTP_400_BAD_REQUEST)

                data_keys = list(data_to_insert.keys())
                for key in data_keys:
                    val = data_to_insert[key]
                    insert_date_time_list = []
                    date_time = dowell_time()
                    insert_date_time = date_time["current_time"] #datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    insert_date_time_list.insert(0, insert_date_time)
                    data_to_insert[f"{key}_operation"] = {"insert_date_time": insert_date_time_list, 'is_deleted': False, 'data_type':data_type}

                inserted_data = new_collection.insert_one(data_to_insert)

                return Response({"success": True, "message": "Data inserted successfully!",
                                "data": {"inserted_id": str(inserted_data.inserted_id)}},
                                status=status.HTTP_201_CREATED)

        except ValidationError as ve:
            return Response({"success": False, "message": str(ve), "data": []},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            traceback.print_exc()
            return Response({"success": False, "message": str(e), "data": []},
                            status=status.HTTP_400_BAD_REQUEST)

            
    def put(self, request, *args, **kwargs):
        try:
            serializer = InputPutSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            database = data.get('db_name')
            coll = data.get('coll_name')
            operation = data.get('operation')
            data_type = data.get('data_type')
            query = data.get('query', {})
            update_data = data.get('update_data', {})
            api_key = data.get('api_key')
            payment = data.get('payment', True)

            for key, value in query.items():
                if key in ["id", "_id"]:
                    try:
                        query[key] = ObjectId(value)
                    except Exception as ex:
                        print(ex)
                        pass

            cluster = settings.MONGODB_CLIENT
            mongoDb = settings.METADATA_COLLECTION.find_one({"database_name": database})

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                    "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            mongodb_coll = settings.METADATA_COLLECTION.find_one(
                {"database_name": database, "collection_names": {"$in": [coll]}})

            if not mongodb_coll:
                return Response(
                    {"success": False, "message": f"Collection '{coll}' does not exist in Datacube database",
                    "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            new_db = cluster["datacube_" + database]
            new_collection = new_db[coll]

            if operation not in ["update"]:
                return Response({"success": False, "message": "Operation not allowed", "data": []},
                                status=status.HTTP_405_METHOD_NOT_ALLOWED)
                
            if data_type not in serializer.choose_data_type:
                return Response({"success": False, "message": "Data type not allowed", "data": []},
                                status=status.HTTP_405_METHOD_NOT_ALLOWED)

            if payment:
                res = check_api_key(api_key)

                if res != "success":
                    return Response(
                        {"success": False, "message": res,
                        "data": []},
                        status=status.HTTP_404_NOT_FOUND)

                existing_document_count = new_collection.count_documents(query)

                if existing_document_count > 10000:
                    return Response(
                        {"success": False, "message": f"10,000 number of documents reached in '{coll}' collection",
                        "data": []},
                        status=status.HTTP_400_BAD_REQUEST)

                field_count = len(update_data)
                if field_count > 10000:
                    return Response({"success": False, "message": f"Number of fields exceeds the limit of 10,000 per document",
                                    "data": []}, status=status.HTTP_400_BAD_REQUEST)
                    
            existing_document = new_collection.find_one(query)      

            modified_count = 0
            existing_operation = existing_document.get(key, {})     
                            
            if existing_document:         
                for key, value in update_data.items():
                    
                    if key not in mongodb_coll['field_labels']:
                        return Response(
                        {"success": False, "message": f"New added field '{key}' is not registered in metadata collection",
                        "data": []},
                        status=status.HTTP_400_BAD_REQUEST)
                    
                    if not key.endswith("_operation") and not existing_document.get(key):
                        existing_document[key] = update_data[key]
                        insert_date_time_list = []
                        date_time = dowell_time()
                        insert_date_time = date_time["current_time"] #datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                        insert_date_time_list.insert(0, insert_date_time)
                        existing_document[f"{key}_operation"] = {"insert_date_time": insert_date_time_list, 'is_deleted': False, 'data_type':data_type}
                            
                for key, value in existing_document.items():                    
                    if key.endswith("_operation"):
                        existingValue = existing_document.get(key.replace('_operation', ''))
                        updatedValue = update_data.get(key.replace('_operation', ''))
                        isDeleted = existing_document.get(key).get('is_deleted')
                        existing_operation = existing_document.get(key, {})
                        
                        if existing_operation["data_type"] == data_type:
                            
                            if existingValue != updatedValue and not isDeleted:
                                if updatedValue is not None:  
                                    date_time = dowell_time()
                                    update_date_time = date_time["current_time"] #datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                                    if isinstance(existing_operation, dict):  
                                        existing_operation.setdefault("update_date_time", []).insert(0, update_date_time)
                                    else:
                                        existing_operation = {"update_date_time": [update_date_time]}  # If not a dictionary, create a new one
                                
                                    existing_document[key.replace('_operation', '')] = updatedValue
                                    modified_count += 1
                        else:
                            return Response({"success": False, "message": f"Got data_type: '{data_type}' But Expected data_type: '{existing_operation['data_type']}' ",
                                            "data": []}, status=status.HTTP_400_BAD_REQUEST)

                result = new_collection.replace_one({"_id": existing_document["_id"]}, existing_document)
                modified_count = result.modified_count

                                
            return Response(
                {"success": True, "message": f"{modified_count} documents updated successfully!",
                "data": []},
                status=status.HTTP_200_OK)
                
        except ValidationError as ve:
            return Response({"success": False, "message": str(ve), "data": []},
                            status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            traceback.print_exc()
            return Response({"success": False, "message": str(e), "data": []},
                            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            serializer = InputDeleteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            database = data.get('db_name')
            coll = data.get('coll_name')
            operation = data.get('operation')
            data_type = data.get('data_type')
            query = data.get('query', {})
            api_key = data.get('api_key')

            for key, value in query.items():
                if key in ["id", "_id"]:
                    try:
                        query[key] = ObjectId(value)
                    except Exception as ex:
                        print(ex)
                        pass

            cluster = settings.MONGODB_CLIENT

            mongoDb = settings.METADATA_COLLECTION.find_one({"database_name": database})

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                    "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            mongodb_coll = settings.METADATA_COLLECTION.find_one({"collection_names": {"$in": [coll]}})
            if not mongodb_coll:
                return Response(
                    {"success": False, "message": f"Collection '{coll}' does not exist in Datacube database",
                    "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            new_db = cluster["datacube_" + database]
            new_collection = new_db[coll]

            if operation != "delete":
                return Response({"success": False, "message": "Operation not allowed", "data": []},
                                status=status.HTTP_405_METHOD_NOT_ALLOWED)
                
            if data_type not in serializer.choose_data_type:
                return Response({"success": False, "message": "Data type not allowed", "data": []},
                                status=status.HTTP_405_METHOD_NOT_ALLOWED)

            res = check_api_key(api_key)
            if res != "success":
                return Response(
                    {"success": False, "message": res,
                    "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            existing_document = new_collection.find_one(query)
            modified_count = 0
            if existing_document:
                for key, value in existing_document.items():
                    if key.endswith("_operation"):
                        # existingValue  = existing_document.get(key.replace('_operation', ''))
                        # updatedValue  = query.get(key.replace('_operation', ''))
                        existing_operation = existing_document.get(key, {})
                        if existing_operation["data_type"]==data_type:
                            isDeleted = existing_document.get(key).get('is_deleted')
                            if not isDeleted:
                                date_time = dowell_time()
                                deleted_date_time = date_time["current_time"] #datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                                existing_operation.setdefault("deleted_date_time", []).insert(0, deleted_date_time)
                                existing_operation['is_deleted']=True
                                # existing_operation["data_type"]=data_type
                                
                                result = new_collection.update_one(query, {"$set": {key: existing_operation}})   
                                modified_count = result.modified_count
                                
                                if "deleted_date_time" not in existing_operation:
                                    existing_operation["deleted_date_time"] = [deleted_date_time] 
                        else:
                            return Response({"success": False, "message": f"Got data_type: '{data_type}' But Expected data_type: '{existing_operation['data_type']}' ",
                                                 "data": []}, status=status.HTTP_400_BAD_REQUEST)
                               

            return Response(
                {"success": True, "message": f"{modified_count} documents deleted successfully!",
                "data": []},
                status=status.HTTP_200_OK)
        except Exception as e:
            traceback.print_exc()
            return Response({"success": False, "message": str(e), "data": []},
                            status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class GetDataView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            database = request.GET.get('db_name')
            coll = request.GET.get('coll_name')
            operation = request.GET.get('operation')
            api_key = request.GET.get('api_key')
            filters_json = request.GET.get('filters')
            filters = json.loads(filters_json) if filters_json else {}
            limit = int(request.GET.get('limit')) if 'limit' in request.GET else None
            offset = int(request.GET.get('offset')) if 'offset' in request.GET else None
            payment = request.GET('payment', True)

            for key, value in filters.items():
                if key in ["id", "_id"]:
                    try:
                        filters[key] = ObjectId(value)
                    except Exception as ex:
                        print(ex)
                        pass

            # config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
            cluster = settings.MONGODB_CLIENT


            # start_time = time.time()
            mongoDb = settings.METADATA_COLLECTION.find_one({"database_name": database})
            # end_time = time.time()
            # print(f"fetch operation find one coll took: {measure_execution_time(start_time, end_time)} seconds")

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            mongodb_coll = settings.METADATA_COLLECTION.find_one({"collection_names": {"$in": [coll]}})
            if not mongodb_coll:
                return Response(
                    {"success": False, "message": f"Collection '{coll}' does not exist in Datacube database",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            new_db = cluster["datacube_" + database]
            new_collection = new_db[coll]

            if operation not in ["fetch"]:
                return Response({"success": False, "message": "Operation not allowed", "data": []},
                                status=status.HTTP_405_METHOD_NOT_ALLOWED)
            if payment:
                res = check_api_key(api_key)

                if res != "success":
                    return Response(
                        {"success": False, "message": res,
                         "data": []},
                        status=status.HTTP_404_NOT_FOUND)

            result = None
            if operation == "fetch":
                query = new_collection.find(filters)
                if offset is not None:
                    query = query.skip(offset)
                if limit is not None:
                    query = query.limit(limit)
                result = query
            result = list(result)
            for doc in result:
                doc['_id'] = str(doc['_id'])
            if len(result) > 0:
                msg = "Data found!"
            else:
                msg = "No data exists for this query/collection"

            return Response({"success": True, "message": msg, "data": result}, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response({"success": False, "message": str(e), "data": []},
                            status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        try:
            serializer = InputGetSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            database = data.get('db_name')
            coll = data.get('coll_name')
            operation = data.get('operation')
            data_type = data.get('data_type')
            api_key = data.get('api_key')
            filters = serializer.validated_data.get('filters', {})
            limit = int(data.get('limit')) if 'limit' in data else None
            offset = int(data.get('offset')) if 'offset' in data else None
            payment = data.get('payment', True)
            
            for key, value in filters.items():
                if key == "_id":
                    try:
                        filters[key] = ObjectId(value)
                    except Exception as ex:
                        print(ex)
                        pass

            cluster = settings.MONGODB_CLIENT

            mongoDb = settings.METADATA_COLLECTION.find_one({"database_name": database})

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                    "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            mongodb_coll = settings.METADATA_COLLECTION.find_one({"collection_names": {"$in": [coll]}})
            if not mongodb_coll:
                return Response(
                    {"success": False, "message": f"Collection '{coll}' does not exist in Datacube database",
                    "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            new_db = cluster["datacube_" + database]
            new_collection = new_db[coll]

            if operation not in ["fetch"]:
                return Response({"success": False, "message": "Operation not allowed", "data": []},
                                status=status.HTTP_405_METHOD_NOT_ALLOWED)
            
            if data_type not in serializer.choose_data_type:
                return Response({"success": False, "message": "Data type not allowed", "data": []},
                                status=status.HTTP_405_METHOD_NOT_ALLOWED)
                
            if payment:
                res = check_api_key(api_key)
                if res != "success":
                    return Response(
                        {"success": False, "message": res,
                        "data": []},
                        status=status.HTTP_404_NOT_FOUND)
                    
            result = None
            if operation == "fetch":
                query = new_collection.find(filters)
                if offset is not None:
                    query = query.skip(offset)
                if limit is not None:
                    query = query.limit(limit)
                result = list(query)
                for doc in result:
                    doc['_id'] = str(doc['_id'])
                    date_time = dowell_time()
                    fetch_date_time = date_time["current_time"] #datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    keys_to_delete = []
                    for key in list(doc.keys()):
                        if key.endswith("_operation"):
                            operation_data = doc[key]
                            if doc[key]['data_type']==data_type:
                                
                                if operation_data.get("is_deleted", False):
                                    keys_to_delete.append(key)
                                    keys_to_delete.append(key[:-len("_operation")])
                                elif not 'fetch_date_time' in operation_data:
                                    operation_data['fetch_date_time'] = [fetch_date_time]
                                    update_query = {
                                        "$set": {
                                            key + ".fetch_date_time": operation_data["fetch_date_time"]
                                        }
                                    }
                                    new_collection.update_one({"_id": ObjectId(doc['_id'])}, update_query)
                                elif 'fetch_date_time' in operation_data and not operation_data["is_deleted"]:
                                    operation_data['fetch_date_time'].insert(0, fetch_date_time)
                                    update_query = {
                                        "$set": {
                                            key + ".fetch_date_time": operation_data["fetch_date_time"]
                                        }
                                    }
                                    new_collection.update_one({"_id": ObjectId(doc['_id'])}, update_query)
                            else:
                                return Response({"success": False, "message": f"Got data_type: '{data_type}' But Expected data_type: '{doc[key]['data_type']}' ",
                                                 "data": []}, status=status.HTTP_400_BAD_REQUEST)

                    for key in keys_to_delete:
                        if key in doc:
                            del doc[key]

            if len(result) > 0 and all("_id" in doc and len(doc) > 1 for doc in result):
                msg = "Data found!"
            else:
                msg = "No data exists for this query/collection"
                return Response({"success": True, "message": msg, "data": []}, status=status.HTTP_200_OK)
            
            return Response({"success": True, "message": msg, "data": result}, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response({"success": False, "message": str(e), "data": []}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class CollectionView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            serializer = GetCollectionsSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            database = data.get('db_name')
            api_key = data.get('api_key')
            payment = data.get('payment', True)

            if payment:
                res = check_api_key(api_key)
                if res != "success":
                    return Response(
                        {"success": False, "message": res,
                         "data": []},
                        status=status.HTTP_404_NOT_FOUND)
            
            cluster = settings.MONGODB_CLIENT
            start_time = time.time()
            mongoDb = settings.METADATA_COLLECTION.find_one({"database_name": database})

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube", "data": []},
                    status=status.HTTP_404_NOT_FOUND)
            
            cluster = settings.MONGODB_CLIENT
            db = cluster["datacube_metadata"]
            coll = db['metadata_collection']

            # Query MongoDB for metadata records associated with the user ID
            metadata_records = coll.find({"database_name":database})

            collections = []
            for record in metadata_records:
                # Add this line for debugging
                collections.append(record.get('collection_names', []))
     
            return Response(
                {"success": True, "message": f"Collections found!", "data": collections},
                status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e), "data": []}, status=status.HTTP_400_BAD_REQUEST)



@method_decorator(csrf_exempt, name='dispatch')
class AddCollection(APIView):
    def post(self, request, *args, **kwargs):
        try:
            serializer = AddCollectionPOSTSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            database = data.get('db_name')
            coll_names = data.get('coll_names')
            api_key = data.get('api_key')
            mongoDb = settings.METADATA_COLLECTION.find_one({"database_name": database})

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            mongodb_coll = settings.METADATA_COLLECTION.find_one({"collection_names": {"$in": [coll_names]}})
            if mongodb_coll:
                return Response(
                    {"success": False, "message": f"Collection with name '{coll_names}' already exists",
                     "data": []},
                    status=status.HTTP_400_BAD_REQUEST)

            res = check_api_key(api_key)
            if res != "success":
                return Response(
                    {"success": False, "message": res,
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            final_data = {
                "number_of_collections": int(data.get('num_collections')),
                "collection_names": coll_names.split(','),
                "added_by": ''
            }

            # Check if the provided 'dbname' exists in the 'database_name' field
            collections = settings.METADATA_COLLECTION.find_one({"database_name": database})

            if collections:
                # Append collections to the existing 'metadata_collection' document
                existing_collections = collections.get("collection_names", [])
                new_collections = final_data.get("collection_names", [])

                for new_collection_name in new_collections:
                    if new_collection_name in existing_collections:
                        return Response(
                            {"success": False,
                             "message": f"Collection `{new_collection_name}` already exists in Database '{database}'",
                             "data": []},
                            status=status.HTTP_409_CONFLICT)

                    pattern = re.compile(r'^[A-Za-z0-9_-]*$')
                    match = pattern.match(new_collection_name)
                    if not match:
                        return Response(
                            {"success": False,
                             "message": f"Collection name `{new_collection_name}` should contain only Alphabet, Numberic OR Underscore",
                             "data": []},
                            status=status.HTTP_404_NOT_FOUND)

                # Combine and remove duplicates
                updated_collections = list(
                    set(existing_collections + new_collections))

                settings.METADATA_COLLECTION.update_one(
                    {"database_name": database},
                    {"$set": {"collection_names": updated_collections}}
                )

            else:
                # Create a new 'metadata_collection' document for the database
                settings.METADATA_COLLECTION.insert_one({
                    "database_name": database,
                    "collection_names": final_data["collection_names"],
                    "number_of_collections": final_data["number_of_collections"],
                    "added_by": final_data["added_by"]
                })

            return Response(
                {"success": True, "message": f"Collection added successfully!",
                 "data": []},
                status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e), "data": []},
                            status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class AddDatabase(APIView):
    def post(self, request, *args, **kwargs):
        try:
            if request.method == 'POST':
                serializer = AddDatabasePOSTSerializer(data=request.data)
                if serializer.is_valid():
                    validated_data = serializer.validated_data
                    username = validated_data.get('username')
                    api_key = validated_data.get('api_key')
                    
                    res = check_api_key(api_key)
                    if res != "success":
                        return Response(
                            {"success": False, "message": res,
                            "data": []},
                            status=status.HTTP_404_NOT_FOUND)
                    if not username:
                        return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)

                    cluster = settings.MONGODB_CLIENT
                    db = cluster["datacube_metadata"]
                    coll = db['metadata_collection']
                    
                    final_data = {
                        "api_key": str(validated_data.get('api_key')),
                        "number_of_collections": int(validated_data.get('num_collections')),
                        "database_name": str(validated_data.get('db_name').lower()),
                        "number_of_documents": int(validated_data.get('num_documents')),
                        "number_of_fields": int(validated_data.get('num_fields')),
                        "field_labels": validated_data.get('field_labels'),
                        "collection_names": validated_data.get('coll_names'),
                        "region_id": validated_data.get('region_id'),
                        "added_by": username,
                        "session_id": validated_data.get('session_id'),
                    }

                    database = coll.find_one({"database_name": str(validated_data.get('db_name').lower())})
                    if database:
                        return Response({'error': 'Database with the same name already exists!'}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        coll.insert_one(final_data)
                        return Response(
                            {"success": True, "message": "Database added successfully!", "data": []},
                            status=status.HTTP_200_OK)
                                  
                else:
                    return Response( { "success": False, "message": serializer.errors, "data": [] }, status=status.HTTP_400_BAD_REQUEST )
            else:
                return Response( { "success": False, "error": 'Method not allowed' }, status=status.HTTP_405_METHOD_NOT_ALLOWED )
        except Exception as e:
            return Response({"success": False, "message": str(e), "data": []}, status=status.HTTP_400_BAD_REQUEST)
