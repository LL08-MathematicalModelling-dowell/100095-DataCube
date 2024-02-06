import pymongo
from bson import ObjectId
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.views import APIView
from pathlib import Path
from django.conf import settings
from .serializers import *
import json
from rest_framework.response import Response
from .helpers import check_api_key
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import re
import time


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

            config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
            cluster = pymongo.MongoClient(host=config['mongo_path'])
            db = cluster['datacube_metadata']
            collection = db['metadata_collection']

            mongoDb = collection.find_one({"database_name": database})

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            mongodb_coll = collection.find_one({"collection_names": {"$in": [coll]}})
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
            return Response({"success": False, "message": e.args[0], "data": []},
                            status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        try:
            serializer = InputPostSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            database = data.get('db_name')
            coll = data.get('coll_name')
            operation = data.get('operation')
            data_to_insert = data.get('data', {})
            api_key = data.get('api_key')

            # if (operation == "fetch") or ("filters" in data):
            #     return DataCrudView.get(self, request, *args, **kwargs)

            config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
            cluster = pymongo.MongoClient(host=config['mongo_path'])
            db = cluster['datacube_metadata']
            collection = db['metadata_collection']

            mongoDb = collection.find_one({"database_name": database})

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            mongodb_coll = collection.find_one({"collection_names": {"$in": [coll]}})
            if not mongodb_coll:
                return Response(
                    {"success": False, "message": f"Collection '{coll}' does not exist in Datacube database",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            new_db = cluster["datacube_" + database]
            new_collection = new_db[coll]

            if operation not in ["insert"]:
                return Response({"success": False, "message": "Operation not allowed", "data": []},
                                status=status.HTTP_405_METHOD_NOT_ALLOWED)

            res = check_api_key(api_key)
            if res != "success":
                return Response(
                    {"success": False, "message": res,
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            if operation == "insert":
                total_documents = new_collection.count_documents({})
                if total_documents >= 10000:
                    return Response(
                        {"success": False,
                         "message": f"Sorry, You can add maximum 10,000 documents inside {coll} collection.",
                         "data": []},
                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    inserted_data = new_collection.insert_one(data_to_insert)
            return Response(
                {"success": True, "message": "Data inserted successfully!",
                 "data": {"inserted_id": str(inserted_data.inserted_id)}},
                status=status.HTTP_201_CREATED)
        except ValidationError as ve:
            return Response({"success": False, "message": str(ve), "data": []},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"success": False, "message": e.args[0], "data": []},
                            status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            serializer = InputPutSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            database = data.get('db_name')
            coll = data.get('coll_name')
            operation = data.get('operation')
            query = data.get('query', {})
            update_data = data.get('update_data', {})
            api_key = data.get('api_key')

            for key, value in query.items():
                if key in ["id", "_id"]:
                    try:
                        query[key] = ObjectId(value)
                    except Exception as ex:
                        print(ex)
                        pass

            config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
            cluster = pymongo.MongoClient(host=config['mongo_path'])
            db = cluster['datacube_metadata']
            collection = db['metadata_collection']

            mongoDb = collection.find_one({"database_name": database})

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            mongodb_coll = collection.find_one({"collection_names": {"$in": [coll]}})
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
            res = check_api_key(api_key)

            if res != "success":
                return Response(
                    {"success": False, "message": res,
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            result = new_collection.update_many(query, {"$set": update_data})
            return Response(
                {"success": True, "message": f"{result.modified_count} documents updated successfully!",
                 "data": []},
                status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": e.args[0], "data": []},
                            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            serializer = InputDeleteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            database = data.get('db_name')
            coll = data.get('coll_name')
            operation = data.get('operation')
            query = data.get('query', {})
            api_key = data.get('api_key')

            for key, value in query.items():
                if key in ["id", "_id"]:
                    try:
                        query[key] = ObjectId(value)
                    except Exception as ex:
                        print(ex)
                        pass
            config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
            cluster = pymongo.MongoClient(host=config['mongo_path'])
            db = cluster['datacube_metadata']
            collection = db['metadata_collection']

            mongoDb = collection.find_one({"database_name": database})

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            mongodb_coll = collection.find_one({"collection_names": {"$in": [coll]}})
            if not mongodb_coll:
                return Response(
                    {"success": False, "message": f"Collection '{coll}' does not exist in Datacube database",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            new_db = cluster["datacube_" + database]
            new_collection = new_db[coll]

            if operation not in ["delete"]:
                return Response({"success": False, "message": "Operation not allowed", "data": []},
                                status=status.HTTP_405_METHOD_NOT_ALLOWED)

            res = check_api_key(api_key)
            if res != "success":
                return Response(
                    {"success": False, "message": res,
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            result = new_collection.delete_many(query)
            return Response(
                {"success": True, "message": f"{result.deleted_count} documents deleted successfully!", "data": []},
                status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": e.args[0], "data": []},
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

            config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
            cluster = pymongo.MongoClient(host=config['mongo_path'])
            db = cluster['datacube_metadata']
            collection = db['metadata_collection']

            mongoDb = collection.find_one({"database_name": database})

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            mongodb_coll = collection.find_one({"collection_names": {"$in": [coll]}})
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
            return Response({"success": False, "message": e.args[0], "data": []},
                            status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
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

            config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
            cluster = pymongo.MongoClient(host=config['mongo_path'])
            db = cluster['datacube_metadata']
            collection = db['metadata_collection']

            mongoDb = collection.find_one({"database_name": database})

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            mongodb_coll = collection.find_one({"collection_names": {"$in": [coll]}})
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
            return Response({"success": False, "message": e.args[0], "data": []},
                            status=status.HTTP_400_BAD_REQUEST)


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
            config = json.loads(
                Path(str(settings.BASE_DIR) + '/config.json').read_text())
            cluster = pymongo.MongoClient(host=config['mongo_path'])

            db = cluster['datacube_metadata']
            coll = db['metadata_collection']
            mongoDb = coll.find_one({"database_name": database})

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

            db_coll = cluster["datacube_" + database]
            collections_list = db_coll.list_collection_names()
            return Response(
                {"success": True, "message": f"Collections found!",
                 "data": collections_list},
                status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": e.args[0], "data": []},
                            status=status.HTTP_400_BAD_REQUEST)


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

            config = json.loads(
                Path(str(settings.BASE_DIR) + '/config.json').read_text())
            cluster = pymongo.MongoClient(host=config['mongo_path'])
            db = cluster['datacube_metadata']
            coll = db['metadata_collection']

            mongoDb = coll.find_one({"database_name": database})

            if not mongoDb:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube",
                     "data": []},
                    status=status.HTTP_404_NOT_FOUND)

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
            collections = coll.find_one({"database_name": database})

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

                coll.update_one(
                    {"database_name": database},
                    {"$set": {"collection_names": updated_collections}}
                )
            else:
                # Create a new 'metadata_collection' document for the database
                coll.insert_one({
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
            return Response({"success": False, "message": e.args[0], "data": []},
                            status=status.HTTP_400_BAD_REQUEST)
