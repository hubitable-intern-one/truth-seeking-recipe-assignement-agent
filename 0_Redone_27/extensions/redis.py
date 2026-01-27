import os
import redis
import logging

# 1. Get Config
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 2. Connect to Redis
try:
    # We use a connection pool for better performance
    pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)
    redis_client = redis.Redis(connection_pool=pool)
    
    # Test the connection immediately
    redis_client.ping()
    print("✅ Connected to Redis")

except Exception as e:
    print(f"❌ Redis Connection Failed: {e}")
    # We don't raise here strictly, so the app can start even if Redis is hiccups
    redis_client = None