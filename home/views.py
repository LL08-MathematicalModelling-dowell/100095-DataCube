import csv
from pathlib import Path
import json
import pymongo
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
import requests
from django.conf import settings
from dbdetails.script import MongoDatabases


def login_view(request):
    try:
        url_id = request.GET.get('session_id', None)
        if url_id:
            request.session["session_id"] = url_id
            return redirect("/")
        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


def index(request):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("username"):
                context = {'page': 'Add Metadata', 'segment': 'index', 'is_admin': False}
                html_template = loader.get_template('home/metadata.html')
                return HttpResponse(html_template.render(context, request))
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")

        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except Exception as e:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


def signout(request):
    d = request.session.get("session_id")
    if d:
        try:
            del request.session["session_id"]
            return redirect("https://100014.pythonanywhere.com/sign-out")
        except:
            return redirect("https://100014.pythonanywhere.com/sign-out")
    else:
        return redirect("https://100014.pythonanywhere.com/sign-out")


# @login_required(login_url='/login/')
def data_view(request):
    try:
        session_id = request.session.get("session_id")
        if session_id:
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": session_id})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("username"):
                is_admin = False

                mongodb = MongoDatabases()
                # databases = mongodb.get_all_databases()
                config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
                cluster = pymongo.MongoClient(host=config['mongo_path'])
                db = cluster['metadata']
                coll = db['metadata_collection']
                databases = coll.find({"added_by": user.get("userinfo", {}).get("username")}, {"database_name": 1})
                databases = [x.get('database_name') for x in databases]

                collections = []
                for d in databases:
                    try:

                        colls = mongodb.get_all_database_collections(d)
                        collections.extend(colls)
                    except Exception:
                        continue

                context = {'page': 'Data View', 'segment': 'data', 'collections': collections, 'is_admin': is_admin,
                           'databases': databases}
                html_template = loader.get_template('home/data-view.html')
                return HttpResponse(html_template.render(context, request))
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")

        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


# @login_required(login_url='/login/')
@csrf_exempt
def metadata_view(request):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("username"):
                if request.method == 'POST':
                    config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
                    cluster = pymongo.MongoClient(host=config['mongo_path'])
                    db = cluster['metadata']
                    coll = db['metadata_collection']

                    final_data = {
                        "number_of_collections": int(request.POST.get('numCollections')),
                        "database_name": str(request.POST.get('databaseName')),
                        "number_of_documents": int(request.POST.get('numDocuments')),
                        "number_of_fields": int(request.POST.get('numFields')),
                        "field_labels": request.POST.get('fieldLabels').split(','),
                        "collection_names": request.POST.get('colNames').split(','),
                        "added_by": user.get("userinfo", {}).get("username"),
                        "session_id": request.session.get("session_id"),
                    }
                    database = coll.find_one({"database_name": str(request.POST.get('databaseName'))})
                    if database:
                        context = {'page': 'Add Metadata', 'segment': 'index', 'is_admin': False, 'error_message': 'Database with the same name already exists!'}
                        html_template = loader.get_template('home/metadata.html')
                        return HttpResponse(html_template.render(context, request)) 
                    else:
                        coll.insert_one(final_data)

                    return redirect(f"{settings.MY_BASE_URL}/retrieve_metadata/")

                context = {'page': 'Add Metadata', 'segment': 'metadata', 'is_admin': False}
                html_template = loader.get_template('home/metadata.html')
                return HttpResponse(html_template.render(context, request))
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")

        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


# @login_required(login_url='/login/')
def retrieve_metadata(request):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("username"):
                config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
                client = pymongo.MongoClient(host=config['mongo_path'])
                db = client['metadata']
                coll = db['metadata_collection']

                # Query MongoDB for metadata records associated with the user ID
                metadata_records = coll.find({"added_by": user.get("userinfo", {}).get("username"), })

                records = []
                for record in metadata_records:
                    # Add this line for debugging

                    records.append({

                        'collection_names': ', '.join(record['collection_names']),
                        'database_name': record['database_name'],
                        'number_of_collections': record['number_of_collections'],  # Add this line
                        'number_of_documents': record['number_of_documents'],  # Add this line
                        'number_of_fields': record['number_of_fields'],
                        'added_by': user.get("userinfo", {}).get("username"),
                    })

                user = request.user
                is_admin = user.is_superuser
                context = {'page': 'Retrieve Metadata', 'segment': 'metadata', 'is_admin': is_admin, 'records': records}
                html_template = loader.get_template('home/retrieve_metadata.html')
                return HttpResponse(html_template.render(context, request))
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")
        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


def retrieve_collections(request, dbname):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("username"):
                config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
                client = pymongo.MongoClient(host=config['mongo_path'])
                db = client['metadata']
                coll = db['metadata_collection']
                user_id = request.user.id  # Get the ID of the currently logged-in user

                # Query MongoDB for metadata records associated with the user ID and the specified 'dbname'
                metadata_records = coll.find(
                    {"added_by": user.get("userinfo", {}).get("username"), "database_name": dbname})

                records = []
                collection_names = []
                total_collections = 0
                for record in metadata_records:
                    collection_names = record['collection_names']
                    # Split the collection names by comma and count the number of items
                    total_collections = len(collection_names)

                    records.append({
                        'collection_names': ', '.join(record['collection_names']),
                        'number_of_collections': total_collections,
                        'added_by': user.get("userinfo", {}).get("username"),
                    })

                user = request.user
                is_admin = user.is_superuser
                context = {'page': 'Retrieve Collections', 'segment': 'metadata', 'is_admin': is_admin,
                           'records': records,
                           'dbname': dbname, 'collection_names': collection_names,
                           'total_collections': total_collections}
                html_template = loader.get_template('home/collections.html')
                return HttpResponse(html_template.render(context, request))
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")
        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


@csrf_exempt
def add_collections(request, dbname):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("username"):
                if request.method == 'POST':
                    config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
                    client = pymongo.MongoClient(host=config['mongo_path'])
                    db = client['metadata']  # Use the provided 'dbname' as the database name
                    coll = db['metadata_collection']

                    final_data = {
                        "number_of_collections": int(request.POST.get('numCollections')),
                        "collection_names": request.POST.get('colNames').split(','),
                        "added_by": user.get("userinfo", {}).get("username"),
                    }

                    # Check if the provided 'dbname' exists in the 'database_name' field
                    collections = coll.find_one({"database_name": dbname})

                    if collections:
                        # Append collections to the existing 'metadata_collection' document
                        existing_collections = collections.get("collection_names", [])
                        new_collections = final_data.get("collection_names", [])

                        # Combine and remove duplicates
                        updated_collections = list(set(existing_collections + new_collections))

                        coll.update_one(
                            {"database_name": dbname},
                            {"$set": {"collection_names": updated_collections}}
                        )
                    else:
                        # Create a new 'metadata_collection' document for the database
                        coll.insert_one({
                            "database_name": dbname,
                            "collection_names": final_data["collection_names"],
                            "number_of_collections": final_data["number_of_collections"],
                            "added_by": final_data["added_by"]
                        })

                    return redirect('home:retrieve_collections', dbname=dbname)

                user = request.user
                is_admin = user.is_superuser
                context = {'page': 'Add Collections', 'segment': 'metadata', 'is_admin': is_admin, 'dbname': dbname}

                return render(request, 'home/collections.html', context)
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")
        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


@csrf_exempt
def settings_view(request):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("username"):
                if request.method == 'POST':
                    config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
                    cluster = pymongo.MongoClient(host=config['mongo_path'])
                    db = cluster['metadata']
                    coll = db['metadata_collection']

                    database_name = request.POST.get('databaseName')
                    collection_name = request.POST.get('colName')
                    field_labels = []
                    file = request.FILES.get('fileToImport')
                    collection_names = [collection_name]

                    final_data = {
                        "database_name": database_name,
                        "collection_name": collection_name,
                        "collection_names": collection_names,
                        "number_of_collections": len(collection_names),
                        "number_of_documents": 1,
                        "field_labels": field_labels,
                        "number_of_fields": len(field_labels),
                        "added_by": user.get("userinfo", {}).get("username"),
                        "session_id": request.session.get("session_id"),
                    }

                    database = coll.find_one({"database_name": database_name})
                    if database:
                        coll.update_one(
                            {"database_name": str(request.POST.get('databaseName'))},
                            {"$set": final_data}
                        )
                    else:
                        coll.insert_one(final_data)

                    # Now create the database and collection in mongodb and insert data
                    db = cluster[str(database_name)]
                    coll = db[str(collection_name)]

                    if file:
                        if file.name.endswith('.json'):
                            json_data = json.loads(file.read())
                            for item in json_data:
                                coll.insert_one(item)

                        elif file.name.endswith('.csv'):
                            csv_reader = csv.DictReader(file.read().decode('utf-8').splitlines())
                            for row in csv_reader:
                                coll.insert_one(row)
                    else:
                        coll.insert_one({"test": "test"})
                else:
                    mongodb = MongoDatabases()
                    config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
                    cluster = pymongo.MongoClient(host=config['mongo_path'])
                    db = cluster['metadata']
                    coll = db['metadata_collection']
                    databases = coll.find({"added_by": user.get("userinfo", {}).get("username")}, {"database_name": 1})
                    databases = [x.get('database_name') for x in databases]

                    collections = []
                    for d in databases:
                        try:

                            colls = mongodb.get_all_database_collections(d)
                            collections.extend(colls)
                        except Exception:
                            continue

                context = {'page': 'DB Import File', 'segment': 'settings', 'is_admin': False, 'collections': collections,
                           'databases': databases}
                html_template = loader.get_template('home/settings.html')
                return HttpResponse(html_template.render(context, request))
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")
        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except Exception as e:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


# @login_required(login_url='/login/')
# def retrieve_metadata(request):
#     try:
#         session_id = request.session.get("session_id")
#         if session_id:
#             url = "https://100014.pythonanywhere.com/api/userinfo/"
#             resp = requests.post(url, data={"session_id": session_id})
#             user = json.loads(resp.text)
#             if user.get("userinfo", {}).get("username"):
#                 config = json.loads(Path(str(settings.BASE_DIR) + '/config.json').read_text())
#                 cluster = pymongo.MongoClient(host=config['mongo_path'])
#                 db = cluster['metadata']
#                 coll = db['metadata_collection']

#                 # Query MongoDB for metadata records associated with the user ID
#                 metadata_records = coll.find({"added_by": user.get("userinfo", {}).get("username")})

#                 records = []
#                 for record in metadata_records:
#                     # print("Current Record:", record)  # Add this line for debugging

#                     records.append({
#                         'database_name': record['database_name'],
#                         'collection_names': ', '.join(record['collection_names']),
#                         'number_of_collections': record['number_of_collections'],  # Add this line
#                         'number_of_documents': record['number_of_documents'],  # Add this line
#                         'number_of_fields': record['number_of_fields'],
#                         'added_by': record.get('added_by'),
#                     })
#                 print("recored L", records)

#                 context = {'page': 'Retrieve Metadata', 'segment': 'retrieve_metadata', 'is_admin': False,
#                            'records': records}
#                 html_template = loader.get_template('home/retrieve_metadata.html')
#                 return HttpResponse(html_template.render(context, request))
#             else:
#                 return redirect(f"{settings.MY_BASE_URL}/logout/")

#         else:
#             return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
#     except:
#         return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
