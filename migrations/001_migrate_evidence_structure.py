import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.getcwd())

# Load environment variables
load_dotenv()

def migrate():
    print("Starting migration: 001_migrate_evidence_structure")
    
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "recipe_crawler")
    
    if not MONGO_URI:
        print("Error: MONGO_URI not set")
        return

    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    collection = db.recipe_contexts
    
    # logic to find documents that need migration
    # We look for documents where 'evidence' is an array, 
    # and the first element (if partial) has 'notes' field directly (old structure)
    # New structure has 'query' and 'evidence_items'
    
    cursor = collection.find({"evidence": {"$type": "array", "$ne": []}})
    
    count = 0
    updated_count = 0
    
    for doc in cursor:
        count += 1
        evidence = doc.get("evidence", [])
        
        if not evidence:
            continue
            
        first_item = evidence[0]
        
        # Check if it's the old structure (has 'notes' directly)
        if "notes" in first_item and "evidence_items" not in first_item:
            print(f"Migrating document {doc['_id']}")
            
            # Wrap all old items into a single "legacy" query group
            new_structure = [
                {
                    "query": "legacy_migration_data",
                    "evidence_items": evidence
                }
            ]
            
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"evidence": new_structure}}
            )
            updated_count += 1
            
    print(f"Migration complete. Scanned {count} docs, updated {updated_count} docs.")

if __name__ == "__main__":
    migrate()
