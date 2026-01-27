import os
from dotenv import load_dotenv
from extensions.mongo import meals_collection, recipe_contexts_collection
from extensions.redis import redis_client

load_dotenv()

def trigger_jobs():
    print("🔍 Scanning for un-analyzed meals...")
    
    # 1. Get all meal IDs
    all_meals = set(doc["_id"] for doc in meals_collection.find({}, {"_id": 1}))
    
    # 2. Get all already analyzed IDs
    analyzed_meals = set(doc["meal_id"] for doc in recipe_contexts_collection.find({}, {"meal_id": 1}))
    
    # 3. Find the difference
    missing_ids = list(all_meals - analyzed_meals)
    
    print(f"📊 Found {len(missing_ids)} meals needing analysis.")
    
    if len(missing_ids) == 0:
        print("🎉 Everything is up to date!")
        return

    # 4. Push to Redis Queue
    count = 0
    for m_id in missing_ids:
        redis_client.rpush("meal_jobs", str(m_id))
        count += 1
        
    print(f"🚀 Successfully queued {count} jobs!")

if __name__ == "__main__":
    trigger_jobs()