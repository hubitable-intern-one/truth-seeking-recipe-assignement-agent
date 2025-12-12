import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.getcwd())

# Load environment variables
load_dotenv()

def migrate():
    print("Starting migration: 002_add_user_context_fields")
    
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "recipe_crawler")
    
    if not MONGO_URI:
        print("Error: MONGO_URI not set")
        return

    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    collection = db.recipe_contexts
    
    # Update documents adding user_scenarios if missing
    print("Checking for missing user_scenarios...")
    result_scenarios = collection.update_many(
        {"user_scenarios": {"$exists": False}},
        {"$set": {"user_scenarios": []}}
    )
    print(f"Added user_scenarios to {result_scenarios.modified_count} documents")

    # Update documents adding user_details if missing
    print("Checking for missing user_details...")
    result_details = collection.update_many(
        {"user_details": {"$exists": False}},
        {"$set": {"user_details": []}}
    )
    print(f"Added user_details to {result_details.modified_count} documents")
    
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
