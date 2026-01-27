import os
import redis
import logging
from dotenv import load_dotenv

load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")

try:
    pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)
    redis_client = redis.Redis(connection_pool=pool)
    redis_client.ping()
    print("Redis Connection established")

except Exception as e:
    print(f"Redis Connection Failed: {e}")
    redis_client = None