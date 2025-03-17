from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["space_station"]
items_collection = db["items"]
logs_collection = db["logs"]