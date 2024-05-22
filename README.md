# DoWell DataCube from DoWell UX Living Lab

Welcome to the DoWell DataCube! The DoWell DataCube is a platform that offers centralized data management, enabling users to create custom databases and access them through APIs.
This documentation contains in-depth information on how to utilize the DoWell DataCube API for data insertion, retrieval and updation.

## Getting Started

To begin using the DataCube API, you need to generate an API key. The process is seamless and straightforward. Follow the steps below to create your API key:

1. Visit the DoWell website at [www.uxlivinglab.com](https://dowellstore.org/).
2. Navigate to the API section and click on "Get API Key."

## API Description

Use of these APIs allows you to interact with a database and perform CRUD operations such as fetching data, inserting data and updating data.

# Steps to use DoWell DataCube and APIs
There are two main steps to use DoWell DataCube


## Step 1: Add request for database
To submit a request for the database, please begin by logging into DataCube. You can access the login page by clicking on the following link: [DataCube Login](https://uxlive.online/). <br>
Once you have successfully logged in, you will be redirected to the dashboard. From there, you can enter your request for the database.

![Dashboard](screenshots/dashboard.jpg)
<br>
<br>
After submitting your request for the database, you'll have the ability to view the created database and its associated collections. <br>
By clicking on "View Collection," you can access and inspect all the collections within the relevant database. <br>
Moreover, you also have the option to add additional collections and fields to the database if needed

![Metadata Records](screenshots/metadata_record.jpg)

ADD NEW COLLECTION
![Add Collections](screenshots/add_collections_to_database.jpg)

ADD NEW FIELD
![Add fields](screenshots/add_fields_to_database.jpg)
<br>
<br>
* import JSON or CSV files feature under development**
<!-- You also have the option to import JSON or CSV files to add documents to a collection.
![Import File](screenshots/import_file.jpg) -->
<br>
<br>

You can also view the data in a data view by selecting the database and collection from the dropdown menu.
![Data View](screenshots/data_view.jpg)
<br>
<br>

After adding the database and collection, you can now utilize APIs to add, retrieve, and update data within the database.

## Step 2: Use Database using APIs

# API Detailed Documentation
=============================================================================
## Allow Data Types
```
"data_type": "real_data" 
       
"data_type": "testing_data" 
    
"data_type": "learning_data" 
   
"data_type": "deleted_data"  
```

## Fetch Data Using the API

### URL: https://uxlive.online/db_api/get_data/
### Method: POST

This API enables you to retrieve data from a specific collection in the Dowell database based on a query.

#### Request Data / API Payload

```json
{
    "api_key": "your-dowell-api-key",
    "db_name": "dowell",
    "coll_name": "test",
    "operation": "fetch",
    "data_type": "real_data",
    "filters": {
         "_id": "664cf185ac91b6cab59e64f9"
    },
    "limit": 1,
    "offset": 0
}
```

#### Parameters

- `api_key` (required): Your Dowell API key.
- `db_name`: The name of the database.
- `coll_name`: The name of the collection to fetch data from.
- `operation`: The operation type, which is "fetch" for this request.
- `data_type`: The data type, which is "real_data" for this request.
- `filters`: A JSON object specifying the query criteria.
- `limit` (optional): The maximum number of records to retrieve per page.
- `offset` (optional): The page number for pagination.

#### Example of Fetching Data in Python

```python
import requests
import json

url = "https://uxlive.online/db_api/get_data/"

data = {
    "api_key": "your-dowell-api-key",
    "db_name": "dowell",
    "coll_name": "test",
    "operation": "fetch",
    "data_type": "real_data",
    "filters": {"_id": "664cf185ac91b6cab59e64f9"},
    "limit": 1,
    "offset": 0
}

response = requests.post(url, json=data)
print(response.text)
```

#### Response:

- For success: `{"data": "[]"}` (an empty array in this example)
- For error: `{"message": "Database not found"}`

## Insert Data

### URL: https://uxlive.online/db_api/crud/
### Method: POST

Use this API to add data to a specific collection within the Dowell database.

#### Request Data / API Payload

```json
{
    "api_key": "your-dowell-api-key",
    "db_name": "dowell",
    "coll_name": "test",
    "operation": "insert",
    "data_type": "real_data",
    "data": {
        "first_name":"milan",
        "last_name":"jakhaniya"
  }
}
```

#### Parameters

- `api_key` (required): Your Dowell API key.
- `db_name`: The name of the database.
- `coll_name`: The name of the collection for data insertion.
- `operation`: The operation type, which is "insert" for this request.
- `data_type`: The data type, which is "real_data" for this request.
- `data`: The data to be inserted as a JSON object.

#### Example of Inserting Data in Python

```python
import requests
import json

url = "https://uxlive.online/db_api/crud/"

data = {
    "api_key": "your-dowell-api-key",
    "db_name": "dowell",
    "coll_name": "test5",
    "operation": "insert",
    "data_type": "real_data",
    "data": {
        "first_name":"milan",
        "last_name":"jakhaniya"
  }
}

response = requests.post(url, json=data)
print(response.text)
```

#### Response:

- For success: `{"message": "Data inserted successfully!"}`
- For error: `{"message": "Database not found"}`

**Note: If a user tries to add more than 10,000 documents in the same collection, the following error will be received:**

For error: `{"message": "Sorry, 10,000 number of documents reached in 'your collection name'"}`

## Update Data

### URL: https://uxlive.online/db_api/crud/
### Method: PUT

Use this API to update data in a specific collection within the Dowell database.

#### Request Data / API Payload

```json
{
    "api_key": "your-dowell-api-key",
    "db_name": "dowell",
    "coll_name": "test",
    "operation": "update",
    "data_type": "real_data",
    "query": {"_id": "664cf185ac91b6cab59e64f9"},
    "update_data": {
        "age":"36"
    }
}
```

#### Parameters

- `api_key` (required): Your DoWell API key.
- `db_name`: The name of the database.
- `coll_name`: The name of the collection to update data in.
- `operation`: The operation type, which is "update" for this request.
- `data_type`: The data type, which is "real_data" for this request.
- `query`: Query or filter the record you want to update.
- `update_data`: The data to be updated, is provided as a JSON object.

#### Example of Updating Data in Python

```python
import requests
import json

url = "https://uxlive.online/db_api/crud/"

data = {
    "api_key": "your-dowell-api-key",
    "db_name": "dowell",
    "coll_name": "test",
    "operation": "update",
    "data_type": "real_data",
    "query" : {"_id": "664cf185ac91b6cab59e64f9"}
    "update_data": {
        "age":"36"
    }
}

response = requests.put(url, json=data)
print(response.text)

```

#### Response:

- For success: `{"message": "1 document updated successfully!"}`
- For error: `{"message": "Database not found"}`

## Delete Data

### URL: https://uxlive.online/db_api/crud/
### Method: DELETE

Use this API to remove data from a specific collection within the Dowell database.

#### Request Data / API Payload

```json
{
    "api_key": "your-dowell-api-key",
    "db_name": "dowell",
    "coll_name": "test",
    "operation": "delete",
    "data_type": "real_data",
    "query": {
        "id": "664cf185ac91b6cab59e64f9"
    }
}
```

#### Parameters

- `api_key` (required): Your Dowell API key.
- `db_name`: The name of the database.
- `coll_name`: The name of the collection from which data will be deleted.
- `operation`: The operation type, which is "delete" for this request.
- `data_type`: The data type, which is "real_data" for this request.
- `query`: Query or filter the record you want to delete.

#### Example of Deleting Data in Python

```python
import requests
import json
url = "https://uxlive.online/db_api/crud/"

data = {
    "api_key": "your-dowell-api-key",
    "db_name": "dowell",
    "coll_name": "test",
    "operation": "delete",
    "data_type": "real_data",
    "query": {
        "_id": "664cf185ac91b6cab59e64f9",
    }

}
response = requests.delete(url, json=data)
print(response.text)

```

#### Response:

- For success: `{"message": "1 document deleted successfully!"}`
- For error: `{"message": "Database not found"}`

```markdown


### Response Codes

- For success: HTTP 200 OK with a JSON response containing a success message.
- For errors: HTTP status codes such as 404 Not Found or 400 Bad Request with an error message.

**Note:** Ensure you replace placeholders such as `"your-dowell-api-key"` and other specific details with actual values in your requests.

```
This documentation provides a comprehensive guide on how to interact with the Dowell Data Cube API, including fetching data, inserting, updating, and deleting records. Please ensure you have the necessary API key and valid data to perform these operations successfully.
