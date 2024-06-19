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
from dbdetails.script import MongoDatabases, dowell_time
from django.contrib import messages
import pandas as pd
from django.core.paginator import Paginator

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
            
            cluster = settings.MONGODB_CLIENT
            db = cluster["datacube_metadata"]
            coll = db['region_collection']
            db_region_list = coll.find({"is_active": True})
            region_list = []
            for i in db_region_list:
                region_list.append({"country": i["country"], "id": str(i["_id"])})
            
            # region_url = "https://100074.pythonanywhere.com/get-countries-v3/"
            # region_list_response = requests.post(region_url)
            # region_list_data = json.loads(region_list_response.content.decode("utf-8"))

            # region_list = region_list_data['data'][0]['countries']

            # final_region_list = []
            # for db_region in db_region_list:
            #     if db_region.lower() in [region.lower() for region in region_list]:
            #         final_region_list.append(db_region.lower())

            # if 'india' not in final_region_list:
            #     final_region_list.append('india')
                
            if user.get("userinfo", {}).get("userID"):
                context = {'page': 'Add Metadata', 'segment': 'index', 'is_admin': False, "regions": region_list}
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
            if user.get("userinfo", {}).get("userID"):
                is_admin = False

                mongodb = MongoDatabases()
                # databases = mongodb.get_all_databases()
                
                cluster = settings.MONGODB_CLIENT
                db = cluster["datacube_metadata"]
                coll = db['metadata_collection']
                databases = coll.find({"userID": user.get("userinfo", {}).get("userID")}, {"database_name": 1})
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
            if user.get("userinfo", {}).get("userID"):
                if request.method == 'POST':
                    cluster = settings.MONGODB_CLIENT
                    db = cluster["datacube_metadata"]
                    coll = db['metadata_collection']

                    collection_names = request.POST.get('colNames').split(',')
                    if len(collection_names) > 10000:
                        error_msg = "Not allowed more than 10,000 collections"
                        context = {
                            'page': 'Add Metadata',
                            'segment': 'index',
                            'is_admin': False,
                            'error_message': error_msg,
                        }
                        html_template = loader.get_template('home/metadata.html')
                        return HttpResponse(html_template.render(context, request))
                    
                    field_labels = request.POST.get('fieldLabels').split(',')
                    if len(field_labels) > 10000:
                        error_msg = "Not allowed more than 10,000 field labels"
                        context = {
                            'page': 'Add Metadata',
                            'segment': 'index',
                            'is_admin': False,
                            'error_message': error_msg,
                        }
                        html_template = loader.get_template('home/metadata.html')
                        return HttpResponse(html_template.render(context, request))

                    final_data = {
                        "number_of_collections": 10000,
                        "database_name": str(request.POST.get('databaseName').lower()),
                        "number_of_documents": 10000,
                        "number_of_fields": 10000,
                        "field_labels": field_labels,
                        "collection_names": collection_names,
                        "region_id": str(request.POST.get('selected_region')),
                        "userID": user.get("userinfo", {}).get("userID"),
                    }

                    total_coll_count = 10000
                    count = len(final_data["collection_names"])
                    for i in range(total_coll_count):
                        if i >= count:
                            untitled_coll = f'untitled_coll_{i + 1}'
                            final_data["collection_names"].append(untitled_coll)
                    
                    total_field_count = 10000
                    count = len(final_data["field_labels"])
                    for i in range(total_field_count):
                        if i >= count:
                            untitled_field = f'untitled_field_{i + 1}'
                            final_data["field_labels"].append(untitled_field)

                    database = coll.find_one({"database_name": final_data["database_name"]})

                    coll_region = db['region_collection']
                    db_region_list = coll_region.find({"is_active": True})
                    region_list = [{"country": i["country"], "id": str(i["_id"])} for i in db_region_list]

                    if database:
                        context = {
                            'page': 'Add Metadata',
                            'segment': 'index',
                            'is_admin': False,
                            'regions': region_list,
                            'error_message': 'Database with the same name already exists!'
                        }
                        html_template = loader.get_template('home/metadata.html')
                        return HttpResponse(html_template.render(context, request))
                    else:
                        coll.insert_one(final_data)

                    return redirect(f"{settings.MY_BASE_URL}retrieve_metadata/")
                
                cluster = settings.MONGODB_CLIENT
                db = cluster["datacube_metadata"]
                coll = db['region_collection']
                db_region_list = coll.find({"is_active": True})
                region_list = [{"country": i["country"], "id": str(i["_id"])} for i in db_region_list]

                context = {'page': 'Add Metadata', 'segment': 'metadata', 'is_admin': False, 'regions': region_list}
                html_template = loader.get_template('home/metadata.html')
                return HttpResponse(html_template.render(context, request))
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")
        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except Exception as e:
        # Ideally log the exception here for debugging
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


# @login_required(login_url='/login/')
def retrieve_metadata(request):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("userID"):
                
                cluster = settings.MONGODB_CLIENT
                db = cluster["datacube_metadata"]
                coll = db['metadata_collection']

                # Query MongoDB for metadata records associated with the user ID
                metadata_records = coll.find({"userID": user.get("userinfo", {}).get("userID"), })

                records = []
                for record in metadata_records:
                    # Add this line for debugging
                    # print(record,"', '.join(record.get('collection_names', []))",', '.join(record.get('field_labels', [])))

                    records.append({

                        'collection_names': ', '.join(record.get('collection_names', [])),
                        'database_name': record.get('database_name', '').lower(),
                        'number_of_collections': record.get('number_of_collections', 0),  # Add this line
                        'number_of_documents': record.get('number_of_documents', 0),  # Add this line
                        'number_of_fields': record.get('number_of_fields', 0),
                        'field_labels': ', '.join(record.get('field_labels', [])),
                        'added_by': user.get("userinfo", {}).get("username"),
                    })

                
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


def retrieve_collections(request, dbname):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("userID"):
                
                cluster = settings.MONGODB_CLIENT
                db = cluster["datacube_metadata"]
                coll = db['metadata_collection']
                search_query = request.GET.get('search', '')

                metadata_records = coll.find(
                    {"userID": user.get("userinfo", {}).get("userID"), "database_name": dbname}).sort("collection_names")

                records = []
                collection_names = []
                total_collections = 0
                remaining_collections = 10000
                for record in metadata_records:
                    collection_names = record['collection_names']
                    total_collections = len(collection_names)
                    remaining_collections = remaining_collections - total_collections
                    
                    if search_query:
                        collection_names = [name for name in collection_names if search_query.lower() in name.lower()]
                    
                    records.append({
                        'collection_names': ', '.join(record['collection_names']),
                        'number_of_collections': total_collections,
                        'added_by': user.get("userinfo", {}).get("username"),
                    })

                paginator = Paginator(collection_names, 20)  # Show 25 contacts per page.
                page_number = request.GET.get("page")
                page_obj = paginator.get_page(page_number)
                context = {
                    "page_obj": page_obj,
                    'page': 'Retrieve Collections',
                    'segment': 'metadata',
                    'is_admin': False,
                    'records': records,
                    'dbname': dbname,
                    'collection_names': collection_names,
                    'total_collections': total_collections,
                    'remaining_collections': remaining_collections,
                    'search_query': search_query,  # Pass the search query to the template
                }
                html_template = loader.get_template('home/collections.html')
                return HttpResponse(html_template.render(context, request))
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")
        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    
    
def retrieve_fields(request, dbname):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("userID"):
                cluster = settings.MONGODB_CLIENT
                db = cluster["datacube_metadata"]
                coll = db['metadata_collection']
                search_query = request.GET.get('search', '')

                metadata_records = coll.find(
                    {"userID": user.get("userinfo", {}).get("userID"), "database_name": dbname}
                ).sort("field_names")

                records = []
                field_names = []
                total_fields = 0
                remaining_fields = 10000

                for record in metadata_records:
                    field_labels = record.get('field_labels', [])
                    total_fields += len(field_labels)
                    remaining_fields -= len(field_labels)
                    if search_query:
                        field_labels = [name for name in field_labels if search_query.lower() in name.lower()]
                    field_names.extend(field_labels)
                    records.append({
                        'number_of_fields': len(field_labels),
                        'field_labels': ', '.join(field_labels),
                        'added_by': user.get("userinfo", {}).get("username"),
                    })

                paginator = Paginator(field_names, 20)  # Show 25 fields per page.
                page_number = request.GET.get("page")
                page_obj = paginator.get_page(page_number)

                context = {
                    "page_obj": page_obj,
                    'page': 'Retrieve Fields',
                    'segment': 'metadata',
                    'is_admin': False,
                    'records': records,
                    'dbname': dbname,
                    'field_names': field_names,
                    'total_fields': total_fields,
                    'remaining_fields': remaining_fields,
                    'search_query': search_query,
                }
                return render(request, 'home/fields.html', context)
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")
        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


@csrf_exempt
def add_collections(request, dbname):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("userID"):
                if request.method == 'POST':
                    cluster = settings.MONGODB_CLIENT
                    db = cluster["datacube_metadata"]
                    coll = db['metadata_collection']

                    final_data = {
                        "number_of_collections": 10000, # int(request.POST.get('numCollections'))
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
                        
                        if len(updated_collections) > 10000:
                            messages.error(request, "Limit Exceeded: You can only add 10000 collections")
                            return redirect('home:retrieve_collections', dbname=dbname)

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
                            "userID": final_data["userID"]
                        })

                    return redirect('home:retrieve_collections', dbname=dbname)

                context = {'page': 'Add Collections', 'segment': 'metadata', 'is_admin': False, 'dbname': dbname}

                return render(request, 'home/collections.html', context)
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")
        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    
@csrf_exempt
def add_fields(request, dbname):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("userID"):
                if request.method == 'POST':
                    
                    cluster = settings.MONGODB_CLIENT
                    db = cluster["datacube_metadata"]
                    coll = db['metadata_collection']

                    final_data = {
                        "field_labels": request.POST.get('field_labels').split(','),
                        "added_by": user.get("userinfo", {}).get("username"),
                    }

                    collections = coll.find_one({"database_name": dbname})
                    if collections:
                        existing_fields = collections.get("field_labels", [])
                        new_fields = final_data.get("field_labels", [])

                        # Combine and remove duplicates
                        updated_fields = list(set(existing_fields + new_fields))
                        if len(updated_fields) > 10000:
                            messages.error(request, f'Number of field labels exceeds the limit of 10,000')
                        else: 
                            coll.update_one(
                                {"database_name": dbname},
                                {"$set": {"field_labels": updated_fields}}
                            )
                    else:
                        coll.insert_one({
                            "database_name": dbname,
                            "field_labels": final_data["field_labels"],
                            "added_by": final_data["added_by"]
                        })

                    return redirect('home:retrieve_fields', dbname=dbname)

                is_admin = False
                context = {'page': 'Add Fields', 'segment': 'metadata', 'is_admin': is_admin, 'dbname': dbname}

                return render(request, 'home/fields.html', context)
            else:
                return redirect(f"{settings.MY_BASE_URL}/logout/")
        else:
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except:
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


@csrf_exempt
def upload_csv_collections(request, dbname):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("userID"):
                if request.method == 'POST':
                    file = request.FILES.get('fileToImport')
                    if file:
                        cluster = settings.MONGODB_CLIENT
                        db = cluster["datacube_metadata"]
                        coll = db['metadata_collection']

                        db0 = coll.find_one_and_update(
                            {"userID": user.get("userinfo", {}).get("userID"), "database_name": dbname},
                            {"$setOnInsert": {"userID": user.get("userinfo", {}).get("userID"), "database_name": dbname}},
                            upsert=True,
                            return_document=True
                        )

                        df = pd.read_csv(file)
                        new_collection_names = df.columns.tolist()

                        existing_collection_names = db0.get("collection_names", [])

                        for new_collection in new_collection_names:
                            if new_collection not in existing_collection_names:
                                for i, existing_collection in enumerate(existing_collection_names):
                                    if existing_collection.startswith('untitled_coll_'):
                                        old_collection_name = existing_collection
                                        new_collection_name = new_collection

                                        # Rename the collection in db1
                                        db1 = cluster["datacube_" + dbname]
                                        db1_coll_list = db1.list_collection_names()
                                        for db1_coll_name in db1_coll_list:
                                            if db1_coll_name == old_collection_name:
                                                db1[old_collection_name].rename(new_collection)
                                                break

                                        existing_collection_names[i] = new_collection_name
                                        break

                        updated_collection_names = list(dict.fromkeys(existing_collection_names))[:10000]

                        if len(updated_collection_names) > 10000:
                            messages.error(request, "Limit Exceeded: You can only add 10000 collections")
                            return redirect('home:retrieve_collections', dbname=dbname)

                        coll.update_one(
                            {"userID": user.get("userinfo", {}).get("userID"), "database_name": dbname},
                            {"$set": {"collection_names": updated_collection_names}}
                        )

                    messages.success(request, 'Saved CSV Collection Successfully..!!')
                    return redirect('home:retrieve_collections', dbname=dbname)
                else:
                    return redirect(f"{settings.MY_BASE_URL}/logout/")
            else:
                return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")
    

@csrf_exempt
def upload_csv_fields(request, dbname):
    try:
        if not request.session.get("session_id"):
            return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")

        url = "https://100014.pythonanywhere.com/api/userinfo/"
        resp = requests.post(url, data={"session_id": request.session["session_id"]})
        user = json.loads(resp.text)
        if not user.get("userinfo", {}).get("userID"):
            return redirect(f"{settings.MY_BASE_URL}/logout/")

        if request.method == 'POST':
            file = request.FILES.get('fileToImport')
            if not file:
                messages.error(request, "No file uploaded.")
                return redirect('home:retrieve_fields', dbname=dbname)

            cluster = settings.MONGODB_CLIENT
            db = cluster["datacube_metadata"]
            coll = db['metadata_collection']

            db0 = coll.find_one_and_update(
                {"userID": user.get("userinfo", {}).get("userID"), "database_name": dbname},
                {"$setOnInsert": {"userID": user.get("userinfo", {}).get("userID"), "database_name": dbname}},
                upsert=True,
                return_document=True
            )

            df = pd.read_csv(file)
            new_field_names = df.columns.tolist()
            existing_field_names = db0.get("field_labels", [])

            for new_field in new_field_names:
                if new_field not in existing_field_names:
                    renamed = False
                    for i, existing_field in enumerate(existing_field_names):
                        operation_field_name = f"{existing_field}_operation"
                        operation_field = db0.get(operation_field_name, {})
                        
                        if operation_field and not operation_field.get('is_deleted', False):
                            old_field_name = existing_field
                            old_operation_field_name = operation_field_name
                            new_field_name = new_field
                            new_operation_field_name = f"{new_field}_operation"
                            update_date_time = dowell_time()

                            db1 = cluster[f"datacube_{dbname}"]
                            for collection_name in db1.list_collection_names():
                                db1[collection_name].update_many({}, {"$rename": {old_field_name: new_field_name, old_operation_field_name: new_operation_field_name}})
                                
                                if db1[collection_name].count_documents({new_operation_field_name: {"$exists": True}}):
                                    db1[collection_name].update_many(
                                        {new_operation_field_name: {"$exists": True}},
                                        {"$push": {f"{new_operation_field_name}.update_date_time": {"$each": [update_date_time], "$position": 0}}}
                                    )
                                else:
                                    db1[collection_name].update_many(
                                        {new_operation_field_name: {"$exists": True}},
                                        {"$set": {f"{new_operation_field_name}.update_date_time": [update_date_time]}}
                                    )

                            existing_field_names[i] = new_field_name
                            renamed = True
                            break
                        elif existing_field.startswith('untitled_field_'):
                            old_field_name = existing_field
                            new_field_name = new_field
                            new_operation_field_name = f"{new_field}_operation"
                            update_date_time = dowell_time()["current_time"]

                            db1 = cluster[f"datacube_{dbname}"]
                            for collection_name in db1.list_collection_names():
                                db1[collection_name].update_many({}, {"$rename": {old_field_name: new_field_name, operation_field_name: new_operation_field_name}})
                                
                                if db1[collection_name].count_documents({new_operation_field_name: {"$exists": True}}):
                                    db1[collection_name].update_many(
                                        {new_operation_field_name: {"$exists": True}},
                                        {"$push": {f"{new_operation_field_name}.update_date_time": {"$each": [update_date_time], "$position": 0}}}
                                    )
                                else:
                                    db1[collection_name].update_many(
                                        {new_operation_field_name: {"$exists": True}},
                                        {"$set": {f"{new_operation_field_name}.update_date_time": [update_date_time]}}
                                    )

                            existing_field_names[i] = new_field_name
                            renamed = True
                            break

                    if not renamed:
                        existing_field_names.append(new_field)

            updated_field_names = list(dict.fromkeys(existing_field_names))[:10000]

            if len(updated_field_names) > 10000:
                messages.error(request, "Limit Exceeded: You can only add 10,000 fields")
                return redirect('home:retrieve_fields', dbname=dbname)

            coll.update_one(
                {"userID": user.get("userinfo", {}).get("userID"), "database_name": dbname},
                {"$set": {"field_labels": updated_field_names}}
            )

            messages.success(request, 'Saved CSV fields successfully..!!')
            return redirect('home:retrieve_fields', dbname=dbname)
        else:
            return redirect(f"{settings.MY_BASE_URL}/logout/")

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect(f"https://100014.pythonanywhere.com/?redirect_url={settings.MY_BASE_URL}/login/")


@csrf_exempt
def settings_view(request):
    try:
        if request.session.get("session_id"):
            url = "https://100014.pythonanywhere.com/api/userinfo/"
            resp = requests.post(url, data={"session_id": request.session["session_id"]})
            user = json.loads(resp.text)
            if user.get("userinfo", {}).get("userID"):
                if request.method == 'POST':
                    
                    cluster = settings.MONGODB_CLIENT
                    db = cluster["datacube_metadata"]
                    coll = db['metadata_collection']

                    database_name = request.POST.get('databaseName').lower()
                    collection_name = request.POST.get('colName')
                    field_labels = []
                    file = request.FILES.get('fileToImport')
                    collection_names = []
                    metadata_records = coll.find(
                    {"userID": user.get("userinfo", {}).get("userID"), "database_name": database_name})

                    for record in metadata_records:
                        collection_names = record['collection_names']
                        field_labels = record['field_labels']

                    final_data = {
                        "database_name": database_name,
                        # "collection_name": collection_name,
                        "collection_names": collection_names,
                        "number_of_collections": len(collection_names),
                        "number_of_documents": 1,
                        "field_labels": field_labels,
                        "number_of_fields": len(field_labels),
                        "userID": user.get("userinfo", {}).get("userID"),
                        # "session_id": request.session.get("session_id"),
                    }

                    database = coll.find_one({"database_name": database_name})
                    if database:
                        coll.update_one(
                            {"database_name": str(request.POST.get('databaseName').lower())},
                            {"$set": final_data}
                        )
                    else:
                        coll.insert_one(final_data)

                    # Now create the database and collection in mongodb and insert data
                    db = cluster["datacube_"+ str(database_name)]
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

                mongodb = MongoDatabases()
                cluster = settings.MONGODB_CLIENT
                db = cluster["datacube_metadata"]
                coll = db['metadata_collection']
                databases = coll.find({"userID": user.get("userinfo", {}).get("userID")}, {"database_name": 1})
                databases = [x.get('database_name') for x in databases]

                collections = []
                for d in databases:
                    try:

                        colls = mongodb.get_all_database_collections(d)
                        collections.extend(colls)
                    except Exception:
                        continue

                context = {'page': 'DB Import File', 'segment': 'settings', 'is_admin': False,
                           'collections': collections,
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
