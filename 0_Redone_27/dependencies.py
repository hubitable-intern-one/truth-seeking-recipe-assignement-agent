import os
from dataclasses import dataclass
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as redis
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class AgentDependencies:
    """
    Dependencies injected into PydanticAI agents.
    Holds the shared connections for Database, Redis, and HTTP.
    """
    mongo_db: AsyncIOMotorDatabase
    redis_client: redis.Redis
    http_client: httpx.AsyncClient

async def get_dependencies() -> AgentDependencies:
    """
    Factory function to create shared connections.
    Called once per job to prevent opening too many sockets.
    """
    # Get configuration from environment
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "recipe_crawler")
    REDIS_URL = os.getenv("REDIS_URL")
    
    # 1. Create Async MongoDB client
    # Note: We use Motor (Async) here, unlike the Sync PyMongo in extensions/mongo.py
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    
    # 2. Create Async Redis client
    redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
    
    # 3. Create Shared HTTP client (The Browser)
    # This makes the 'Verifier Tool' much faster by reusing the connection
    http_client = httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    
    return AgentDependencies(
        mongo_db=mongo_client[MONGO_DB_NAME],  
        redis_client=redis_client,
        http_client=http_client
    )

async def cleanup_dependencies(deps: AgentDependencies) -> None:
    """
    Cleanup function to properly close connections.
    Crucial for preventing memory leaks in long-running workers.
    """
    if deps.http_client:
        await deps.http_client.aclose()
        
    if deps.redis_client:
        await deps.redis_client.close()
        
    # Motor/Mongo clients manage their own pool, but if we accessed the client
    # strictly through the DB object, we usually leave it open or close the client specifically.
    # For this pattern, closing HTTP and Redis is the priority.