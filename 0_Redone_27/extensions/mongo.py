import os
from pymongo import MongoClient
import logging

MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:password@localhost:27017/")  #! Get Config from .env
DB_NAME = os.getenv("MONGO_DB_NAME", "recipe_crawler") #!Change later on

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    meals_collection = db["meals"]     #? specific "folders" inside database
    recipe_contexts_collection = db["recipe_contexts"]
    jobs_collection = db["jobs"]
    failed_jobs_collection = db["failed_jobs"]

    print(f"Connection established to {DB_NAME}")

except Exception as e:
    print(f"Connection Failed: {e}")
    raise e