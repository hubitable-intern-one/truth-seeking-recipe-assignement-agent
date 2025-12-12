import os
import redis
from rq import Worker, Queue
from dotenv import load_dotenv

# Load env vars
load_dotenv()

listen = ['default']

def start_worker():
    REDIS_URL = os.getenv("REDIS_URL")
    if not REDIS_URL:
        print("Error: REDIS_URL not set in .env")
        return

    conn = redis.from_url(REDIS_URL)

    print("Starting RQ worker...")
    # Instantiate queues with the connection
    queues = [Queue(name, connection=conn) for name in listen]
    # Instantiate worker with the connection
    worker = Worker(queues, connection=conn)
    worker.work()

if __name__ == "__main__":
    start_worker()
