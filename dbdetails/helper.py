import datetime
import os
import os.path
import tarfile
from pathlib import Path

import bson
from pymongo import MongoClient


def create_folder_backup(dbname):
    dt = datetime.datetime.now()
    home = str(Path.home())
    directory = f"{home}/backups/{ dt.now().strftime('%Y-%m-%d %H.%M') }/{dbname}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def run_backup(mongoUri, dbname, colls=None):
    try:
        client = MongoClient(mongoUri)
        db = client[dbname]
        collections = db.list_collection_names()
        if colls:
            collections = [val for val in collections if val in colls]
        directory = create_folder_backup(dbname)

        for coll in collections:
            # Check if file already exists
            file_path = os.path.join(directory, f'{coll}.bson')
            if os.path.exists(file_path):
                print('File already exists!')
                continue
            # Only create a backup if collection has data
            docs = list(db[coll].find({}))

            try:
                if docs:
                    with open(file_path, 'wb+') as f:
                        for doc in db[coll].find():
                            f.write(bson.BSON.encode(doc))

            except Exception as e:
                print("Error: " + str(e))
                pass

        return None

    except Exception as e:
        print("Error: " + str(e))
        return None


def make_tarfile(output_filename, source_dir):
    tar = tarfile.open(output_filename, "w:gz")
    for filename in source_dir:
        tar.add(filename)
    tar.close()


def run_restore(mongoUri, dbname, direc):
    try:
        client = MongoClient(mongoUri)

        # check if database already exists
        db_names = client.list_database_names()
        if dbname in db_names:
            return None

        db = client["backup_" + dbname]
        new_dir = direc + "/" + dbname

        list_of_collections = db.list_collection_names()
        for collec in os.listdir(new_dir):
            try:
                _collection = collec.split('.')[0]

                # don't restore if collection already exist
                if _collection in list_of_collections:
                    continue

                collection = db[_collection]

                if collec.endswith('.bson'):
                    with open(os.path.join(new_dir, collec), 'rb+') as f:
                        collection.insert_many(bson.decode_all(f.read()))
            except Exception as e:
                print("Error: " + str(e))
                pass
        return None
    except Exception as e:
        return None
