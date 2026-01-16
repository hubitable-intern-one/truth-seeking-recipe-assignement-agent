import sys
import os
from rq import Worker, Queue, Connection
from dotenv import load_dotenv

# 1. Import your shared connection
# This ensures if you change settings in extensions/redis.py, the worker updates too.
from extensions.redis import get_redis_connection

# Load env vars
load_dotenv()

# Add project root to path so the worker can find 'jobs.py' and 'agents/'
sys.path.append(os.getcwd())

listen = ['default']

def start_worker():
    # 2. Use the shared factory function
    conn = get_redis_connection()

    print(f"🚀 Worker started. Listening on queues: {listen}")
    
    # 3. The 'Connection' context manager makes code cleaner
    # It tells RQ: "Use this connection for everything inside this block"
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()

if __name__ == "__main__":
    start_worker()




# import os
# import redis
# from rq import Worker, Queue
# from dotenv import load_dotenv

# # Load env vars
# load_dotenv()

# listen = ['default']

# def start_worker():
#     REDIS_URL = os.getenv("REDIS_URL")
#     if not REDIS_URL:
#         print("Error: REDIS_URL not set in .env")
#         return

#     conn = redis.from_url(REDIS_URL)

#     print("Starting RQ worker...")
#     # Instantiate queues with the connection
#     queues = [Queue(name, connection=conn) for name in listen]
#     # Instantiate worker with the connection
#     worker = Worker(queues, connection=conn)
#     worker.work()

# if __name__ == "__main__":
#     start_worker()
