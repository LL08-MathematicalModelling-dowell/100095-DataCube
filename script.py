import json
import os
from datetime import datetime
from pathlib import Path
from django.conf import settings

import bson
import pymongo


class BackupScript:
    def __init__(self):
        self.cluster = settings.MONGODB_CLIENT

    def create_folder_backup(self, dbname):
        dt = datetime.now()
        home = str(Path.home())
        directory = f"{home}/backups/{dt.now().strftime('%Y-%m-%d %H.%M')}/{dbname}"
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

    def run_backup(self, client, dbname):
        try:
            db = client[dbname]
            collections = db.list_collection_names()

            directory = self.create_folder_backup(dbname)
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

    def get_backup(self):
        try:
            conn = self.cluster

            for db_name in conn.list_database_names():
                try:
                    self.run_backup(conn, db_name)
                except Exception as e:
                    print("Exception in Backup : ", str(e))
                    pass

            print("Backup completed successfully")
        except Exception as e:
            print("Exception : ", str(e))


if __name__ == "__main__":
    ld = BackupScript()
    ld.get_backup()
