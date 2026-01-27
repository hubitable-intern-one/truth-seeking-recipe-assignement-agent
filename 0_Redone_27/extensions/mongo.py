import os
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "recipe_crawler")

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