import os
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Redis configuration from environment
REDIS_URL = os.getenv("REDIS_URL")

# Create Redis client
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Queue name for recipe processing jobs
QUEUE_NAME = "recipe_agent_jobs"

# Test connection
def test_connection():
    """Test Redis connection"""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False

# Helper functions for queue operations
def enqueue_recipe(recipe_id):
    """Add a recipe ID to the processing queue"""
    return redis_client.rpush(QUEUE_NAME, recipe_id)

def dequeue_recipe():
    """Get the next recipe ID from the queue (blocking)"""
    return redis_client.blpop(QUEUE_NAME, timeout=0)

def get_queue_length():
    """Get the current length of the queue"""
    return redis_client.llen(QUEUE_NAME)

def peek_queue(count=10):
    """Peek at the first N items in the queue without removing them"""
    return redis_client.lrange(QUEUE_NAME, 0, count - 1)

def clear_queue():
    """Clear all items from the queue"""
    return redis_client.delete(QUEUE_NAME)
