import os
import redis
from rq import Queue
from dotenv import load_dotenv
from extensions.mongo import meals_collection, recipe_contexts_collection
from jobs import process_meal


load_dotenv()

def trigger_jobs():
    """
    Uses an aggregation pipeline to fetch meals that do NOT have
    a matching recipe_context. 
    """

    REDIS_URL = os.getenv("REDIS_URL")
    if not REDIS_URL:
        print("Error: REDIS_URL not set in .env")
        return

    # Connect to Redis queue
    conn = redis.from_url(REDIS_URL)
    q = Queue(connection=conn)

    print("Checking for unprocessed meals...")


    pipeline = [
        {
            "$lookup": {
                "from": "recipe_contexts",
                "localField": "_id",
                "foreignField": "meal_id",
                "as": "ctx"
            }
        },
        {
            "$match": {
                "ctx": {"$size": 0}   
            }
        },
        {
            "$project": {
                "_id": 1,
                "title": 1
            }
        }
    ]

    unprocessed_meals = meals_collection.aggregate(pipeline)
    count_enqueued = 0

    for meal in unprocessed_meals:
        meal_id = meal["_id"]

        print(f"Enqueueing meal: {meal.get('title', meal_id)}")
        q.enqueue(process_meal, meal_id, job_timeout='10m')
        count_enqueued += 1

    print(f"Trigger complete. Enqueued {count_enqueued} new jobs.")

if __name__ == "__main__":
    trigger_jobs()
