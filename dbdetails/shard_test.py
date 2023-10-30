'''
Sample code snippet for sharding
'''
#Connect to the mongo process using Mongo class
from pymongo import MongoClient
client = MongoClient("mongodb://<hostname>:<port>")


#Enable sharding using the enableSharding method:
db = client.admin
result = db.command("enableSharding", "<database>")

#Creating a sharded collection while specifying the sharding key
db = client."<database>"
result = db.createCollection("<collection>", shardKey="<key>")

#insert data into sharded collection
db.<collection>.insert_one({"<key>": "<value>", ...})

#Querying the sharded collection
result = db.<collection>.find({"<key>": "<value>"})
