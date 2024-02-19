import datetime
import io
import json
import os
from pathlib import Path

import openpyxl
import pymongo
from bson import ObjectId
from django.conf import settings
from django.http import HttpResponse
from rest_framework.status import (HTTP_200_OK, HTTP_400_BAD_REQUEST)

from .helper import run_backup, run_restore

from pymongo import MongoClient
from bson.json_util import dumps

class MongoDatabases:
    def __init__(self):
        self.client = MongoClient(settings.MONGODB_URI)

    def get_all_databases(self):
        try:
            database_list = self.client.list_database_names()
            return database_list
        except Exception as e:
            print("Exception: ", str(e))
            return None

    def get_all_database_collections(self, database):
        try:
            dbc = self.client[database]
            cols = dbc.list_collection_names()
            return cols
        except Exception as e:
            print("Exception: ", str(e))
            return None
        
    def iterate_over_databases(self, db_names):
        try:
            data_array = []
            for db_name in db_names:
                data_array = self.get_all_database_collections_and_date_diff(db_name, data_array)
            return data_array
        except Exception as e:
            print("Exception : ", str(e))
            return None

    def iterate_over_cluster(self):
        try:
            data_array = []
            db_names = self.cluster.list_database_names()
            for db_name in db_names:
                data_array.append({"database": db_name, "collection": "", "days_diff": ""})
                data_array = self.get_all_database_collections_and_date_diff(db_name, data_array, True)
            return data_array
        except Exception as e:
            print("Exception : ", str(e))
            return None

    def get_all_database_collections_and_date_diff(self, db_name, data_array, cluster=None):
        try:
            db = self.cluster[db_name]
            for coll_name in db.list_collection_names():
                try:
                    base = db[coll_name].find({}, {"_id"}).sort("_id", 1).limit(1)
                    date_now = datetime.datetime.now()
                    creation_date = date_now
                    for i in base:
                        creation_date = i["_id"].generation_time
                    naive = creation_date.replace(tzinfo=None)
                    time_diff = date_now - naive
                    days_diff = f'{time_diff.days} days'
                except Exception as e:
                    print("Exception : ", str(e))
                    days_diff = "NA"
                    pass
                if cluster:
                    data_array.append({"database": "", "collection": coll_name, "days_diff": days_diff})
                else:
                    data_array.append({"database": db_name, "collection": coll_name, "days_diff": days_diff})
            return data_array
        except Exception as e:
            print("Exception : ", str(e))
            return None

    def get_documents_count_of_all_collections(self, database):
        try:
            conn = self.cluster
            db = conn[database]
            my_dic = {}
            for coll_name in db.list_collection_names():
                try:
                    count = db[coll_name].count_documents({})
                    my_dic[coll_name] = count
                    print("db: {}, collection:{}, documents:{}".format(database, coll_name, count))
                except Exception as e:
                    print("Exception : ", str(e))
                    pass
            return my_dic
        except Exception as e:
            print("Exception : ", str(e))
            return {}

    def iterate_over_all_database(self):
        try:
            conn = self.cluster
            meta_data = conn[self.database]
            t = datetime.datetime.now()
            meta_col = "database_details_" + t.strftime('%d-%m-%Y')
            meta_coll = meta_data[meta_col]

            for db_name in conn.list_database_names():
                try:
                    db = conn[db_name]
                    for coll_name in db.list_collection_names():
                        try:
                            temp = {}
                            coll_data = []
                            coll_data1 = []
                            count = db[coll_name].count_documents({})
                            temp["database"] = db_name
                            temp["collection"] = coll_name
                            temp["collection_doc_count"] = count
                            base = db[coll_name].find().sort("_id", 1).limit(1)
                            base_keys = []
                            not_unique_record = []
                            for i in base:
                                for k, v in i.items():
                                    base_keys.append(k)
                            for r in db[coll_name].find({}):
                                try:
                                    key_count = 0
                                    coll_data = []
                                    coll_data1 = []
                                    for key, val in r.items():
                                        key_count += 1
                                        if key not in base_keys:
                                            not_unique_record.append(r["_id"])
                                            coll_data.append(r["_id"])

                                    if len(base_keys) != key_count:
                                        coll_data1.append(r["_id"])
                                except Exception as e:
                                    print("Exception : ", str(e))
                                    pass
                        except Exception as e:
                            print("Exception : ", str(e))
                            pass

                        temp["different_record"] = coll_data
                        temp["fields_not_equal"] = coll_data1
                        object_id = meta_coll.insert_one(temp)
                        print("Object Id : ", str(object_id.inserted_id))
                except Exception as e:
                    print("Exception : ", str(e))
                    pass
            return {"status": True, "message": "Job Run Successfully!. "}
        except Exception as e:
            print("Exception : ", str(e))
            return {"status": False, "message": str(e)}

    def get_last_insertion_time_of_all_collections(self):
        try:
            conn = self.cluster
            meta_data = conn[self.database]
            t = datetime.datetime.now()
            meta_col = "last_insertion_time_" + t.strftime('%d-%m-%Y')
            meta_coll = meta_data[meta_col]
            date_now = datetime.datetime.now()
            for db_name in conn.list_database_names():
                try:
                    db = conn[db_name]
                    temp = {}
                    temp["database"] = db_name
                    time_array = []
                    for coll_name in db.list_collection_names():
                        try:
                            base = db[coll_name].find().sort("_id", -1).limit(1)
                            for i in base:
                                date_later = i["_id"].generation_time
                            naive = date_later.replace(tzinfo=None)
                            date_diff = date_now - naive
                            time_array.append(
                                {coll_name: {"last_insertion_time": str(date_later), "days_diff": str(date_diff.days)}})
                        except Exception as e:
                            print("Exception : ", str(e))
                            pass
                    temp["collection_times"] = time_array
                    object_id = meta_coll.insert_one(temp)
                    print("Object Id : ", str(object_id.inserted_id))
                except Exception as e:
                    print("Exception : ", str(e))
                    pass

            return {"status": True, "message": "Job Run Successfully!. "}
        except Exception as e:
            print("Exception : ", str(e))
            return {"status": False, "message": str(e)}

    def get_date_diff_of_all_collections(self):
        data_array = []
        try:
            conn = self.cluster
            date_now = datetime.datetime.now()
            for db_name in conn.list_database_names():
                try:
                    db = conn[db_name]
                    temp = {}
                    temp["database"] = db_name
                    for coll_name in db.list_collection_names():
                        temp["collection"] = coll_name
                        try:
                            base = db[coll_name].find().sort("_id", -1).limit(1)
                            for i in base:
                                date_later = i["_id"].generation_time
                            naive = date_later.replace(tzinfo=None)
                            date_diff = date_now - naive
                            temp["date_diff"] = str(date_diff.days)
                            temp["last_insertion_time"] = str(naive)
                        except Exception as e:
                            print("Exception : ", str(e))
                            temp["date_diff"] = "NA"
                            pass
                        data_array.append(temp)
                except Exception as e:
                    print("Exception : ", str(e))
                    pass

            return {"status": True, "data": data_array, "message": "Job Run Successfully!. "}
        except Exception as e:
            print("Exception : ", str(e))
            return {"status": False, "data": data_array, "message": str(e)}

    def get_backup(self, databases=None, collections=None):
        try:
            conn = self.cluster
            mongoUri = self.config['mongo_path']

            if not databases:
                for db_name in ['BD_DISCUSSION', 'BD_IMAGE', 'hr_hiring']:  # conn.list_database_names():
                    try:
                        run_backup(mongoUri, db_name)
                    except Exception as e:
                        print("Exception in Backup : ", str(e))
                        pass
            else:
                for db_name in databases:  # conn.list_database_names():
                    try:
                        run_backup(mongoUri, db_name, collections)
                    except Exception as e:
                        print("Exception in Backup : ", str(e))
                        pass

            return {"status": True, "message": "Job Run Successfully!. "}
        except Exception as e:
            print("Exception : ", str(e))
            return {"status": False, "message": str(e)}

    def restore(self, date_of_backup):
        try:
            mongoUri = self.config['mongo_path']
            home = str(Path.home())
            directory = (f'{home}/backups/{date_of_backup}')
            for database in os.listdir(directory):
                try:
                    run_restore(mongoUri, database, directory)
                except Exception as e:
                    print("Exception in Backup : ", str(e))
                    pass

            return {"success": True, "message": "Job Run Successfully!. ", "status": HTTP_200_OK}
        except Exception as e:
            print("Exception : ", str(e))
            return {"success": False, "message": str(e), "status": HTTP_400_BAD_REQUEST}

    def delete_collection(self, database, collection):
        try:
            client = self.cluster
            database_list = client.list_database_names()
            if not (database in database_list):
                return {"success": False, "message": f"Please enter a valid database name",
                        "status": HTTP_400_BAD_REQUEST}
            db = client[database]
            list_of_collections = db.list_collection_names()
            if not (collection in list_of_collections):
                return {"success": False, "message": f"Please enter a valid collection name in {database} database",
                        "status": HTTP_400_BAD_REQUEST}
            collection = db[collection]
            collection.drop()

            return {"success": True, "message": "Job Run Successfully!. ", "status": HTTP_200_OK}
        except Exception as e:
            print("Exception : ", str(e))
            return {"success": False, "message": str(e), "status": HTTP_400_BAD_REQUEST}

    def delete_database(self, database):
        try:
            client = self.cluster
            database_list = client.list_database_names()
            if not (database in database_list):
                return {"success": False, "message": f"Please enter a valid database name",
                        "status": HTTP_400_BAD_REQUEST}
            client.drop_database(database)
            return {"success": True, "message": "Job Run Successfully!. ", "status": HTTP_200_OK}

        except Exception as e:
            print("Exception : ", str(e))
            return {"success": False, "message": str(e), "status": HTTP_400_BAD_REQUEST}

    def export_cluster(self):
        database_list = self.cluster.list_database_names()
        data_array = []
        days_diff = 'NA'

        for db_name in database_list:
            try:
                db = self.cluster[db_name]
                for coll_name in db.list_collection_names():
                    try:
                        base = db[coll_name].find({}, {"_id"}).sort("_id", 1).limit(1)
                        date_now = datetime.datetime.now()

                        for i in base:
                            try:
                                obj_id = ObjectId(i["_id"])
                                creation_date = obj_id.generation_time
                                naive = creation_date.replace(tzinfo=None)
                                time_diff = date_now - naive
                                days_diff = f'{time_diff.days} days'

                            except Exception as ex:
                                days_diff = 'NA'

                    except Exception as e:
                        print("Exception : ", str(e))
                        days_diff = "NA"
                        pass

                    data_array.append({"database": db_name, "collection": coll_name, "days_diff": days_diff})
            except Exception as e:
                continue
        workbook = openpyxl.Workbook()
        sheet = workbook.active

        # header
        sheet.append(['Database', 'Collection', 'Used-Since/Days Difference'])

        # append data in excel sheet rows
        for row in data_array:
            sheet.append(list(row.values()))

        # header styling
        header = openpyxl.styles.NamedStyle(name="header")
        header.font = openpyxl.styles.Font(bold=True)
        header.border = openpyxl.styles.Border(bottom=openpyxl.styles.Side(border_style="thin"))
        header.alignment = openpyxl.styles.Alignment(horizontal="center", vertical="center")

        # Now let's apply this to all first row (header) cells
        header_row = sheet[1]
        for cell in header_row:
            cell.style = header

        # Create a BytesIO stream to store the workbook as a binary object
        stream = io.BytesIO()

        # Save the workbook to the BytesIO stream
        workbook.save(stream)

        # Set the file pointer at the beginning of the stream
        stream.seek(0)

        # Create the Blob from the stream data
        blob_data = stream.getvalue()

        # Create the HttpResponse object with appropriate content type and headers
        response = HttpResponse(blob_data,
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="exported_data.xlsx"'

        return response

    def insert_cronjob_in_db(self, cron_name, created_at, _time, interval):
        client = self.cluster
        db = client['cronjob_database']
        collection = db['cron_meta_data']

        # Prepare the document to be inserted
        document = {
            "name": cron_name,
            "created_at": created_at,
            "updated_at": created_at,
            "schedule_time": _time,
            "interval": interval
        }

        # Insert the document
        result = collection.insert_one(document)
        print("Inserted document ID:", result.inserted_id)

