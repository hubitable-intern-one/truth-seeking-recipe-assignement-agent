import os
import redis
from rq import Worker, Queue, Connection
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

    with Connection(conn):
        print("Starting RQ worker...")
        worker = Worker(list(map(Queue, listen)))
        worker.work()

if __name__ == "__main__":
    start_worker()
