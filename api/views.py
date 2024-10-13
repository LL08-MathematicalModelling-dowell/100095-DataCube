import re
import traceback

from bson import ObjectId
from rest_framework import status

from .script import dowell_time
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.views import APIView
from django.core.paginator import Paginator
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_yasg.utils import swagger_auto_schema

from api.helpers import check_api_key
from api.serializers import (
    AddCollectionPOSTSerializer,
    GetCollectionsSerializer,
    AddDatabasePOSTSerializer,
    InputDeleteSerializer,
    InputGetSerializer,
    InputPostSerializer,
    InputPutSerializer,
)
@method_decorator(csrf_exempt, name='dispatch')
class DataCrudView(APIView):
    """
    A view for handling CRUD operations on MongoDB collections.
    """

    def get_serializer_class(self):
        """
        Returns the serializer class based on the request method.
        """
        if self.request.method == 'GET':
            return InputGetSerializer
        elif self.request.method == 'POST':
            return InputPostSerializer
        elif self.request.method == 'PUT':
            return InputPutSerializer
        elif self.request.method == 'DELETE':
            return InputDeleteSerializer

    @swagger_auto_schema(query_serializer=InputGetSerializer, responses={200: InputGetSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to fetch data from a specified MongoDB collection.
        """
        try:
            serializer = InputGetSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            database = data.get('db_name')
            coll = data.get('coll_name')
            operation = data.get('operation')
            # api_key = data.get('api_key')
            filters = self.convert_object_id(data.get('filters', {}))
            limit = data.get('limit', 50)  # Default limit to 50 if not provided
            offset = data.get('offset', 0)  # Default offset to 0 if not provided

            # Validate database and collection existence
            self.validate_database_and_collection(database, coll)

            if operation != "fetch":
                return self.method_not_allowed_response()

            # THIS CODE IS COMMENTED OUT FOR NOW BECAUSE API KEI SYSTEM IS NOT IMPLEMENTED YET AND THE APP IS USED IN-HOUSE
            # API key validation
            # if not self.is_api_key_valid(api_key):
            #     return self.unauthorized_response("Invalid API key")

            # Fetching data
            result = self.fetch_data_from_collection(database, coll, filters, limit, offset)

            msg = "Data found!" if result else "No data exists for this query/collection"
            return Response({"success": True, "message": msg, "data": result}, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response({"success": False, "message": str(e), "data": []}, status=status.HTTP_400_BAD_REQUEST)

    def convert_object_id(self, filters):
        """
        Converts 'id' and '_id' keys in filters to ObjectId.
        """
        for key, value in filters.items():
            if key in ["id", "_id"]:
                try:
                    filters[key] = ObjectId(value)
                except Exception as ex:
                    print(f"Conversion error: {ex}")
        return filters

    def validate_database_and_collection(self, database, coll):
        """
        Validates if the specified database and collection exist.
        """
        mongo_db = settings.METADATA_COLLECTION.find_one({"database_name": database})
        if not mongo_db:
            raise ValueError(f"Database '{database}' does not exist in Datacube")

        if coll not in mongo_db.get("collection_names", []):
            raise ValueError(f"Collection '{coll}' does not exist in Datacube database")

    # THIS CODE IS COMMENTED OUT FOR NOW BECAUSE API KEI SYSTEM IS NOT IMPLEMENTED YET AND THE APP IS USED IN-HOUSE
    # def is_api_key_valid(self, api_key):
    #     """
    #     Validates the provided API key.
    #     """
    #     return check_api_key(api_key) == "success"

    def fetch_data_from_collection(self, database, coll, filters, limit=50, offset=0):
        """
        Fetches data from the specified collection with optional filters, limit, and offset.
        """
        cluster = settings.MONGODB_CLIENT
        new_collection = cluster[f"datacube_{database}"][coll]

        query = new_collection.find(filters).skip(offset).limit(limit)
        result = list(query)

        for doc in result:
            doc['_id'] = str(doc['_id'])  # Convert ObjectId to string for JSON serialization
        return result

    def method_not_allowed_response(self):
        """
        Returns a response indicating that the method is not allowed.
        """
        return Response({"success": False, "message": "Operation not allowed", "data": []}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def unauthorized_response(self, message):
        """
        Returns an unauthorized response with the specified message.
        """
        return Response({"success": False, "message": message, "data": []}, status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(query_serializer=InputPostSerializer, responses={201: 'Created'})
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to insert new data into a specified MongoDB collection.
        """
        try:
            serializer = InputPostSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            database = data.get('db_name')
            coll = data.get('coll_name')
            # api_key = data.get('api_key')
            data_to_insert = data.get('data', {})

            # THIS CODE IS COMMENTED OUT FOR NOW BECAUSE API KEI SYSTEM IS NOT IMPLEMENTED YET AND THE APP IS USED IN-HOUSE
            # Validate API key once
            # if not self.is_api_key_valid(api_key):
            #     return self.unauthorized_response("Invalid API key")

            # Validate database and collection
            self.validate_database_and_collection(database, coll)

            # Check operation
            if data.get('operation') != "insert":
                return self.method_not_allowed_response()

            new_collection = settings.MONGODB_CLIENT[f"datacube_{database}"][coll]

            # Document count check
            if new_collection.count_documents({}) >= 10000:
                return Response({"success": False, "message": f"10,000 document limit reached in '{coll}' collection", "data": []}, status=status.HTTP_400_BAD_REQUEST)

            # Insert the document
            insert_date_time = dowell_time()["current_time"]
            data_to_insert.update({
                f"{key}_operation": {
                    "insert_date_time": [insert_date_time],
                    "is_deleted": False,
                    "data_type": data.get('data_type')
                } for key in data_to_insert.keys()
            })
            inserted_data = new_collection.insert_one(data_to_insert)

            return Response({"success": True, "message": "Data inserted successfully!", "data": {"inserted_id": str(inserted_data.inserted_id)}}, status=status.HTTP_201_CREATED)

        except Exception as e:
            traceback.print_exc()
            return Response({"success": False, "message": str(e), "data": []}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(query_serializer=InputPutSerializer, responses={200: 'Updated'})
    def put(self, request, *args, **kwargs):
        """
        Handles PUT requests to update existing data in a specified MongoDB collection.
        """
        try:
            serializer = InputPutSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            database = data.get('db_name')
            coll = data.get('coll_name')
            operation = data.get('operation')
            data_type = data.get('data_type')
            query = self.convert_object_id(data.get('query', {}))
            update_data = data.get('update_data', {})

            # Validate database and collection
            self.validate_database_and_collection(database, coll)

            if operation != "update":
                return self.method_not_allowed_response()

            if data_type not in serializer.choose_data_type:
                return self.method_not_allowed_response()

            # THIS CODE IS COMMENTED OUT FOR NOW BECAUSE API KEI SYSTEM IS NOT IMPLEMENTED YET AND THE APP IS USED IN-HOUSE
            # API key validation
            # if not self.is_api_key_valid(api_key):
            #     return self.unauthorized_response("Invalid API key")

            new_collection = settings.MONGODB_CLIENT[f"datacube_{database}"][coll]

            # Document existence check
            existing_document = new_collection.find_one(query)
            if not existing_document:
                return Response({"success": False, "message": "No document found matching the query", "data": []}, status=status.HTTP_404_NOT_FOUND)

            # Validate update data and apply updates
            modified_count = self.update_document(existing_document, update_data, data_type)
            new_collection.replace_one({"_id": existing_document["_id"]}, existing_document)

            return Response({"success": True, "message": f"{modified_count} documents updated successfully!", "data": []}, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response({"success": False, "message": str(e), "data": []}, status=status.HTTP_400_BAD_REQUEST)

    def update_document(self, existing_document, update_data, data_type):
        """
        Applies updates to the existing document and returns the count of modified fields.
        """
        modified_count = 0
        for key, value in update_data.items():
            if key not in existing_document:
                raise ValueError(f"Field '{key}' not found in document")
            if existing_document[key] != value:
                existing_document[key] = value
                modified_count += 1
        return modified_count

    @swagger_auto_schema(query_serializer=InputDeleteSerializer, responses={200: 'Deleted'})
    def delete(self, request, *args, **kwargs):
        """
        Handles DELETE requests to remove data from a specified MongoDB collection.
        """
        try:
            serializer = InputDeleteSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            data = serializer.validated_data
            database = data.get('db_name')
            coll = data.get('coll_name')
            operation = data.get('operation')
            data_type = data.get('data_type')
            query = self.convert_object_id(data.get('query', {}))

            # Validate database and collection
            self.validate_database_and_collection(database, coll)

            if operation != "delete":
                return self.method_not_allowed_response()

            if data_type not in serializer.choose_data_type:
                return self.method_not_allowed_response()

            # THIS CODE IS COMMENTED OUT FOR NOW BECAUSE API KEI SYSTEM IS NOT IMPLEMENTED YET AND THE APP IS USED IN-HOUSE
            # API key validation
            # if not self.is_api_key_valid(api_key):
            #     return self.unauthorized_response("Invalid API key")

            new_collection = settings.MONGODB_CLIENT[f"datacube_{database}"][coll]

            # Delete the document
            result = new_collection.delete_one(query)
            if result.deleted_count == 0:
                return Response({"success": False, "message": "No document found matching the query", "data": []}, status=status.HTTP_404_NOT_FOUND)

            return Response({"success": True, "message": "Document deleted successfully", "data": []}, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response({"success": False, "message": str(e), "data": []}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class ListCollectionsView(APIView):
    """
    API view to list all collections for a given database in Datacube.
    The provided API key must match the one stored in the metadata collection.
    """

    @swagger_auto_schema(query_serializer=GetCollectionsSerializer, responses={200: 'Success'})
    def get(self, request, *args, **kwargs):
        try:
            # Validate request data using serializer
            serializer = GetCollectionsSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # Extract database name and API key from request
            database = data.get('db_name')
            # api_key = data.get('api_key')

            # THIS CODE IS COMMENTED OUT FOR NOW BECAUSE API KEI SYSTEM IS NOT IMPLEMENTED YET AND THE APP IS USED IN-HOUSE
            # Validate the provided API key
            # res = check_api_key(api_key)
            # if res != "success":
            #     return Response(
            #         {"success": False, "message": res, "data": []},
            #         status=status.HTTP_404_NOT_FOUND
            #     )

            # Fetch metadata for the specified database
            # mongo_db = settings.METADATA_COLLECTION.find_one({"api_key": api_key})
            mongo_db = settings.METADATA_COLLECTION.find_one({"database_name": database})
            if not mongo_db:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube", "data": []},
                    status=status.HTTP_404_NOT_FOUND
                )

            # THIS CODE IS COMMENTED OUT FOR NOW BECAUSE API KEI SYSTEM IS NOT IMPLEMENTED YET AND THE APP IS USED IN-HOUSE
            # Ensure the provided API key matches the API key stored in metadata
            # if mongo_db.get('database_name') != database:
            #     return Response(
            #         {"success": False, "message": "Invalid API key for the specified database", "data": []},
            #         status=status.HTTP_403_FORBIDDEN
            #     )

            # Establish MongoDB connection
            cluster = settings.MONGODB_CLIENT
            db = cluster["datacube_metadata"]
            coll = db['metadata_collection']

            # Query for collections associated with the specified database
            metadata_record = coll.find_one({"database_name": database})

            if not metadata_record:
                return Response(
                    {"success": False, "message": f"No collections found for database '{database}'", "data": []},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Extract the collection names
            collections = metadata_record.get('collection_names', [])

            # Return the list of collections found
            return Response(
                {"success": True, "message": "Collections found!", "data": collections},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            # Return error response in case of an exception
            return Response(
                {"success": False, "message": str(e), "data": []},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(csrf_exempt, name='dispatch')
class AddCollectionView(APIView):
    """
    API view to handle adding new collections to an existing database in Datacube.
    Validates the API key, checks if the database and collections already exist, and
    creates new collections with valid names.
    """
    serializer_class = AddCollectionPOSTSerializer

    @swagger_auto_schema(query_serializer=AddCollectionPOSTSerializer, responses={201: 'Created'})
    def post(self, request, *args, **kwargs):
        try:
            # Validate the request data
            serializer = AddCollectionPOSTSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            # Extract data from the request
            database = data.get('db_name')
            coll_names = data.get('coll_names').split(',')
            # api_key = data.get('api_key')

            # Validate the API key
            # res = check_api_key(api_key)
            # if res != "success":
            #     return Response(
            #         {"success": False, "message": res, "data": []},
            #         status=status.HTTP_404_NOT_FOUND
            #     )

            # Check if the database exists in the metadata collection
            mongo_db = settings.METADATA_COLLECTION.find_one({"database_name": database})
            if not mongo_db:
                return Response(
                    {"success": False, "message": f"Database '{database}' does not exist in Datacube", "data": []},
                    status=status.HTTP_404_NOT_FOUND
                )

            # THIS CODE IS COMMENTED OUT FOR NOW BECAUSE API KEI SYSTEM IS NOT IMPLEMENTED YET AND THE APP IS USED IN-HOUSE
            # Ensure the provided API key matches the API key stored in metadata
            # if mongo_db.get('api_key') != api_key:
            #     return Response(
            #         {"success": False, "message": "Invalid API key for the specified database", "data": []},
            #         status=status.HTTP_403_FORBIDDEN
            #     )

            # Check if any of the provided collection names already exist in the database
            mongodb_coll = settings.METADATA_COLLECTION.find_one({"collection_names": {"$in": coll_names}})
            if mongodb_coll:
                return Response(
                    {"success": False, "message": f"One or more collections '{coll_names}' already exist", "data": []},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Prepare the final collection data
            final_data = {
                "number_of_collections": data.get('num_collections'),
                "collection_names": coll_names,
            }

            # Check if the collections already exist in the specified database
            collections = settings.METADATA_COLLECTION.find_one({"database_name": database})
            if collections:
                existing_collections = collections.get("collection_names", [])
                new_collections = final_data.get("collection_names", [])

                # Validate and add new collections
                for new_collection_name in new_collections:
                    if new_collection_name in existing_collections:
                        return Response(
                            {"success": False,
                             "message": f"Collection '{new_collection_name}' already exists in Database '{database}'",
                             "data": []},
                            status=status.HTTP_409_CONFLICT
                        )

                    # Validate the collection name format
                    if not re.match(r'^[A-Za-z0-9_-]*$', new_collection_name):
                        return Response(
                            {"success": False,
                             "message": f"Collection name '{new_collection_name}' should only contain alphabets, numbers, or underscores.",
                             "data": []},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                # Merge and update collection names, removing duplicates
                updated_collections = list(set(existing_collections + new_collections))

                settings.METADATA_COLLECTION.update_one(
                    {"database_name": database},
                    {"$set": {"collection_names": updated_collections}}
                )

                # Create the collections in the MongoDB database
                cluster = settings.MONGODB_CLIENT
                if database not in cluster.list_database_names():
                    return Response(
                        {"success": False, "message": f"Database '{database}' does not exist", "data": []},
                        status=status.HTTP_404_NOT_FOUND
                    )

                db = cluster[database]
                for collection_name in new_collections:
                    if collection_name in db.list_collection_names():
                        return Response(
                            {"success": False, "message": f"Collection '{collection_name}' already exists", "data": []},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Create the new collection
                    db.create_collection(collection_name)

                return Response(
                    {"success": True, "message": f"Collections '{', '.join(new_collections)}' created successfully", "data": []},
                    status=status.HTTP_201_CREATED
                )

            else:
                # If the database doesn't exist in metadata, create a new metadata entry
                settings.METADATA_COLLECTION.insert_one({
                    "database_name": database,
                    "collection_names": final_data["collection_names"],
                    "number_of_collections": final_data["number_of_collections"],
                })

            return Response(
                {"success": True, "message": "Collection added successfully!", "data": []},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            # Catch and return any unexpected errors
            return Response(
                {"success": False, "message": str(e), "data": []},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(csrf_exempt, name='dispatch')
class CreateDatabaseView(APIView):
    """
    API view to handle creation of a new database with collections and documents based on the product name.
    The view performs API key validation, database creation, and conditionally adds collections/documents
    based on the product_name "living lab admin".
    """
    serializer_class = AddDatabasePOSTSerializer

    @swagger_auto_schema(query_serializer=AddDatabasePOSTSerializer, responses={200: 'Created'})
    def post(self, request, *args, **kwargs):
        try:
            # Validate the request data
            serializer = AddDatabasePOSTSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            validated_data = serializer.validated_data
            # api_key = validated_data.get('api_key')
            product_name = validated_data.get('product_name', '').lower()
            db_name = validated_data.get('db_name', '').lower()

            # THIS CODE IS COMMENTED OUT FOR NOW BECAUSE API KEI SYSTEM IS NOT IMPLEMENTED YET AND THE APP IS USED IN-HOUSE
            # Validate the API key
            # res = check_api_key(api_key)
            # if res != "success":
            #     return Response(
            #         {"success": False, "message": res, "data": []},
            #         status=status.HTTP_404_NOT_FOUND
            #     )

            # MongoDB setup
            cluster = settings.MONGODB_CLIENT
            metadata_db = cluster["datacube_metadata"]
            metadata_coll = metadata_db['metadata_collection']

            # Check if a database with the same name already exists in metadata
            existing_metadata = metadata_coll.find_one({"database_name": db_name})
            if existing_metadata:
                return Response(
                    {"error": f"Database '{db_name}' with the same name already exists!"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # THIS CODE IS COMMENTED OUT FOR NOW BECAUSE API KEI SYSTEM IS NOT IMPLEMENTED YET AND THE APP IS USED IN-HOUSE
            # Ensure the provided API key matches the one stored in metadata for this database (if it exists)
            # if existing_metadata and existing_metadata.get('api_key') != api_key:
            #     return Response(
            #         {"success": False, "message": "Invalid API key for the specified database", "data": []},
            #         status=status.HTTP_403_FORBIDDEN
            #     )

            # Ensure the database doesn't already exist in the MongoDB cluster
            if db_name in cluster.list_database_names():
                return Response(
                    {"success": False, "message": f"Database '{db_name}' already exists", "data": []},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Insert metadata into the metadata collection
            final_data = {
                # "api_key": api_key,
                "number_of_collections": validated_data.get('num_collections'),
                "database_name": db_name,
                "number_of_documents": validated_data.get('num_documents'),
                "number_of_fields": validated_data.get('num_fields'),
                "field_labels": validated_data.get('field_labels'),
                "collection_names": validated_data.get('coll_names'),
                "region_id": validated_data.get('region_id'),
            }
            metadata_coll.insert_one(final_data)

            # Create the new database in MongoDB
            new_db = cluster[db_name]

            # If the product name is "living lab admin", create specific collections and documents
            if product_name and product_name == "living lab admin":
                self.create_collections_for_living_lab(new_db)
            else:
                collection_names = validated_data.get('coll_names')
                num_collections = validated_data.get('num_collections')
                
                # Create collections from provided names
                for collection_name in collection_names:
                    new_db.create_collection(collection_name)
                
                # Ensure we create the exact number of collections as specified in num_collections
                if len(collection_names) < num_collections:
                    for i in range(len(collection_names), num_collections):
                        new_db.create_collection(f'collection_{i+1}')
                
            return Response(
                {"success": True, "message": "Database and collections created successfully!", "data": []},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            # Handle any exceptions that may occur
            return Response(
                {"success": False, "message": str(e), "data": []},
                status=status.HTTP_400_BAD_REQUEST
            )

    def create_collections_for_living_lab(self, new_db):
        """
        Creates collections and inserts documents for the "living lab admin" product.
        - Collections 1 to 1000 will each have 1 document.
        - Collections 1001 to 10000 will each have 1000 documents.
        """
        try:
            # Create collections 1 to 1000, each with 1 document (using bulk insert for optimization)
            collections_data = []
            for i in range(1, 1001):
                collections_data.append(
                    {
                        "collection_name": f"collection_{i}",
                        "documents": [{"data": f"document_{i}"}]
                    }
                )
            for data in collections_data:
                collection = new_db.create_collection(data["collection_name"])
                collection.insert_many(data["documents"])

            # Create collections 1001 to 10000, each with 1000 documents
            collections_data = []
            for i in range(1001, 10001):
                documents = [{"data": f"document_{j}"} for j in range(1, 1001)]
                collections_data.append(
                    {
                        "collection_name": f"collection_{i}",
                        "documents": documents
                    }
                )
            for data in collections_data:
                collection = new_db.create_collection(data["collection_name"])
                collection.insert_many(data["documents"])

        except Exception as e:
            # Log or handle specific errors related to collection creation
            raise Exception(f"Error while creating collections: {str(e)}")
