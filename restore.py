import json
import os
import re
from pathlib import Path
from django.conf import settings
import bson
import pymongo


class RestoreScript:
    def __init__(self):
        self.cluster = settings.MONGODB_CLIENT
        self.date_pattern = "^\d{4}-\d{2}-\d{2} \d{2}\.\d{2}$"
        self.home = f'{Path.home()}/backups/'

    def run_restore(self, dbname, backup_directory):
        """
        - get or create database with name `backup_{backup_directory}_{dbname}`
        - get all collections of the database and loop through it
        - continue to next iteration if collection already exists in database
        - insert data in mongo if collection has data
        """
        try:
            client = self.cluster

            database = backup_directory + "/" + dbname

            backup_directory = backup_directory.replace(' ', '_').replace('.', '_')
            database_name = f"backup_{backup_directory.split('/')[-1]}_{dbname}"
            db = client[database_name]

            # check if database already exists
            db_names = client.list_database_names()
            if database_name in db_names:
                return None

            list_of_collections = db.list_collection_names()
            for collec in os.listdir(database):
                try:
                    _collection = collec.split('.')[0]

                    # don't restore if collection already exist
                    if _collection in list_of_collections:
                        continue

                    collection = db[_collection]

                    if collec.endswith('.bson'):
                        with open(os.path.join(database, collec), 'rb+') as f:
                            collection.insert_many(bson.decode_all(f.read()))
                except Exception as e:
                    print("Error: " + str(e))
                    pass
            return None
        except Exception as e:
            return None

    def restore_backup_directory(self, backup_name):
        """
        - get all databases in backup_name directory
        - pass a single database and backup_name to run_restore function
        """
        for database in os.listdir(backup_name):
            try:
                self.run_restore(database, backup_name)
            except Exception as e:
                print("Exception in Restore Backup : ", str(e))
                pass

    def validate_dates(self, date_list):
        """
        - filter out backup folders with pattern '2023-5-3 07.02'
        - return the filtered list
        """
        dates = []
        for date in date_list:
            if bool(re.match(self.date_pattern, date)):
                dates.append(date)
        return dates

    def restore_backup(self):
        """
        - match all the backup folders from backup directory with format '2023-5-3 07.02'
        - pass the validated backup directories to restore_backup_directory
        - print message `Restore Backup completed successfully` on successful restore
        """
        try:
            backup_list = self.validate_dates(os.listdir(self.home))
            for backup in backup_list:
                self.restore_backup_directory(f'{self.home}{backup}')

            print("Restore Backup completed successfully")
        except Exception as e:
            print("Exception in Restore Backup : ", str(e))
            return None


if __name__ == "__main__":
    ld = RestoreScript()
    ld.restore_backup()
