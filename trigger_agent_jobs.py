import os
import redis
from rq import Queue
from dotenv import load_dotenv
from extensions.mongo import meals_collection, recipe_contexts_collection
from jobs import process_meal

# Load env vars
load_dotenv()

def trigger_jobs():
    """
    Scans MongoDB for meals that haven't been processed yet 
    and enqueues them for the agent.
    """
    REDIS_URL = os.getenv("REDIS_URL")
    if not REDIS_URL:
        print("Error: REDIS_URL not set in .env")
        return

    # Connect to Redis
    conn = redis.from_url(REDIS_URL)
    q = Queue(connection=conn) # Default queue

    print("Checking for meals to process...")
    
    # 1. Get all meal IDs
    # In a real large-scale app, we would use a more efficient query or status field.
    # Here we simply check if a corresponding recipe_context exists.
    
    meals_cursor = meals_collection.find({}, {"_id": 1, "title": 1})
    
    count_enqueued = 0
    
    for meal in meals_cursor:
        meal_id = meal["_id"]
        
        # Check if already processed
        # exists = recipe_contexts_collection.count_documents({"meal_id": meal_id})
        # Optimization: We could cache processed IDs or use $lookup, but for now simple check is fine.
        
        # Using simple find_one for check
        if recipe_contexts_collection.find_one({"meal_id": meal_id}):
             # print(f"Skipping {meal.get('title')}: Already processed")
             continue
             
        # Enqueue job
        print(f"Enqueueing meal: {meal.get('title', meal_id)}")
        q.enqueue(process_meal, meal_id, job_timeout='10m') # 10 min timeout for agent
        count_enqueued += 1
        
    print(f"Trigger complete. Enqueued {count_enqueued} new jobs.")

if __name__ == "__main__":
    trigger_jobs()
