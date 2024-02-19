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
from django.http import JsonResponse
from pymongo import MongoClient
from django.shortcuts import redirect

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
# def data_view(request):
#     try:
#         session_id = request.session.get("session_id")
#         if session_id:
#             url = "https://100014.pythonanywhere.com/api/userinfo/"
#             resp = requests.post(url, data={"session_id": session_id})
#             user = json.loads(resp.text)
#             if user.get("userinfo", {}).get("username"):
#                 db = MONGODB_CLIENT[MONGODB_DATABASE_NAME]
#                 coll = db['metadata_collection']
#                 # print(coll,"coll",db,"dbdbdbdbdb")

#                 # Query MongoDB for metadata records associated with the user ID
#                 metadata_records = coll.find({"added_by": user.get("userinfo", {}).get("username"), })
                

#                 records = []
#                 for record in metadata_records:
                    
                   

#                     records.append({
#                         'collection_names': ', '.join(record.get('collection_names', [record.get('collection_name', '')])),
#                         'database_name': record.get('database_name', ''),
#                         'number_of_collections': record.get('number_of_collections', 0),
#                         'number_of_documents': record.get('number_of_documents', 0),
#                         'number_of_fields': record.get('number_of_fields', 0),
#                         'added_by': user.get("userinfo", {}).get("username"),
#                     })
#                 print(records)
                    

#                 user = request.user
#                 is_admin = False

#                 context = {'page': 'Data View', 'segment': 'data', 'collections': collections, 'is_admin': is_admin,
#                            'databases': databases}
#                 html_template = loader.get_template('home/data-view.html')
#                 return HttpResponse(html_template.render(context, request))
#             else:
#                 return redirect(f"{settings.MY_BASE_URL}/logout/")

#         else:
#             return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
#     except Exception as e:
#         return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


def data_view(request):
    try:
        session_id = request.session.get("session_id")
        if session_id:
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": session_id})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("username"):
                client = settings.MONGODB_CLIENT
                db = client[settings.MONGODB_DATABASE_NAME]
                coll = db['metadata_collection']

                # Query MongoDB for metadata records associated with the user ID
                metadata_records = coll.find({"added_by": user.get("userinfo", {}).get("username")})

                records = []
                collections = set()
                databases = set()

                for record in metadata_records:
                    collections.update(record.get('collection_names', []))
                    databases.add(record.get('database_name', ''))

                    records.append({
                        'collection_names': ', '.join(record.get('collection_names', [])),
                        'database_name': record.get('database_name', ''),
                        'number_of_collections': record.get('number_of_collections', 0),
                        'number_of_documents': record.get('number_of_documents', 0),
                        'number_of_fields': record.get('number_of_fields', 0),
                        'added_by': user.get("userinfo", {}).get("username"),
                    })

                user = request.user
                is_admin = False

                context = {
                    'page': 'Data View',
                    'segment': 'data',
                    'collections': list(collections),
                    'databases': list(databases),
                    'is_admin': is_admin,
                    'records': records
                }
                html_template = loader.get_template('home/data-view.html')
                return HttpResponse(html_template.render(context, request))
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")
        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except Exception as e:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


##########ok
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
                    client = settings.MONGODB_CLIENT
                    db = client[settings.MONGODB_DATABASE_NAME]
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
                        context = {'page': 'Add Metadata', 'segment': 'index', 'is_admin': False,
                                   'error_message': 'Database with the same name already exists!'}
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
    except Exception as e:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


#########ok
# @login_required(login_url='/login/')
def retrieve_metadata(request):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("username"):
                client = settings.MONGODB_CLIENT
                db = client[settings.MONGODB_DATABASE_NAME]
                coll = db['metadata_collection']

                # Query MongoDB for metadata records associated with the user ID
                metadata_records = coll.find({"added_by": user.get("userinfo", {}).get("username"), })
                

                records = []
                for record in metadata_records:
                    
                   

                    records.append({
                        'collection_names': ', '.join(record.get('collection_names', [record.get('collection_name', '')])),
                        'database_name': record.get('database_name', ''),
                        'number_of_collections': record.get('number_of_collections', 0),
                        'number_of_documents': record.get('number_of_documents', 0),
                        'number_of_fields': record.get('number_of_fields', 0),
                        'added_by': user.get("userinfo", {}).get("username"),
                    })

                user = request.user
                is_admin = False
                context = {'page': 'Retrieve Metadata', 'segment': 'metadata', 'is_admin': is_admin, 'records': records}
                html_template = loader.get_template('home/retrieve_metadata.html')
                return HttpResponse(html_template.render(context, request))
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")
        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except Exception as e:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")

########ok
def retrieve_collections(request, dbname):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("username"):
                client = settings.MONGODB_CLIENT
                db = client[settings.MONGODB_DATABASE_NAME]
                coll = db['metadata_collection']

                # Query MongoDB for metadata records associated with the user ID and the specified 'dbname'
                metadata_records = coll.find(
                    {"added_by": user.get("userinfo", {}).get("username"), "database_name": dbname})

                records = []
                collection_names = []
                total_collections = 0
                for record in metadata_records:
                    collection_names = record['collection_names']
                    total_collections = len(collection_names)

                    records.append({
                        'collection_names': ', '.join(record['collection_names']),
                        'number_of_collections': total_collections,
                        'added_by': user.get("userinfo", {}).get("username"),
                    })

                user = request.user
                is_admin = False
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
    except Exception as e:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")

##################ok
@csrf_exempt
def add_collections(request, dbname):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("username"):
                if request.method == 'POST':
                    client = settings.MONGODB_CLIENT
                    db = client[settings.MONGODB_DATABASE_NAME]
                    coll = db['metadata_collection']

                    final_data = {
                        "number_of_collections": int(request.POST.get('numCollections')),
                        "collection_names": request.POST.get('colNames').split(','),
                        "added_by": user.get("userinfo", {}).get("username"),
                    }

                    collections = coll.find_one({"database_name": dbname})

                    if collections:
                        existing_collections = collections.get("collection_names", [])
                        new_collections = final_data.get("collection_names", [])
                        updated_collections = list(set(existing_collections + new_collections))

                        coll.update_one(
                            {"database_name": dbname},
                            {"$set": {"collection_names": updated_collections}}
                        )
                    else:
                        coll.insert_one({
                            "database_name": dbname,
                            "collection_names": final_data["collection_names"],
                            "number_of_collections": final_data["number_of_collections"],
                            "added_by": final_data["added_by"]
                        })

                    return redirect('home:retrieve_collections', dbname=dbname)

                user = request.user
                is_admin = False
                context = {'page': 'Add Collections', 'segment': 'metadata', 'is_admin': is_admin, 'dbname': dbname}

                return render(request, 'home/collections.html', context)
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")
        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except Exception as e:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


def get_collections_for_user(username, collection, databases):
    collections = {}
    for db_name in databases:
        collections[db_name] = collection.find({"added_by": username, "database_name": db_name})
    return collections

@csrf_exempt
def settings_view(request):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("username"):
                if request.method == 'POST':
                    database_name = request.POST.get('databaseName')
                    collection_name = request.POST.get('colName')


                    client = settings.MONGODB_CLIENT
                    db = client[database_name]
                    coll = db[collection_name]


                    # db = MONGODB_CLIENT[database_name]
                    # coll = db[collection_name]


                    file = request.FILES.get('fileToImport')

                    collection_names = [collection_name]

                    final_data = {
                        "database_name": database_name,
                        "collection_name": collection_name,
                        "collection_names": collection_names,
                        "number_of_collections": len(collection_names),
                        "number_of_documents": 1,
                        "added_by": user.get("userinfo", {}).get("username"),
                        "session_id": request.session.get("session_id"),
                    }

                    database = coll.find_one({"database_name": database_name})
                    if database:
                        coll.insert_one(final_data)
                        # coll.update_one(
                        #     {"database_name": str(request.POST.get('databaseName'))},
                        #     {"$set": final_data}
                        # )
                    # else:
                    #     coll.insert_one(final_data)

                    if file:
                        if file.name.endswith('.json'):
                            json_data = json.loads(file.read().decode('utf-8'))
                            for item in json_data:
                                coll.insert_one(item)
                        elif file.name.endswith('.csv'):
                            csv_reader = csv.DictReader(file.read().decode('utf-8').splitlines())
                            for row in csv_reader:
                                coll.insert_one(row)
                    else:
                        coll.insert_one({"test": "test"})

                client = settings.MONGODB_CLIENT
                db = client[settings.MONGODB_DATABASE_NAME]
                coll = db['metadata_collection']
                databases = coll.find({"added_by": user.get("userinfo", {}).get("username")}, {"database_name": 1})
                databases = [x.get('database_name') for x in databases]

                collections = get_collections_for_user(user.get("userinfo", {}).get("username"), coll, databases)

                context = {
                    'page': 'DB Import File',
                    'segment': 'settings',
                    'is_admin': False,
                    'collections': collections,
                    'databases': databases
                }

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
#                 db = cluster["datacube_metadata" ]
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
