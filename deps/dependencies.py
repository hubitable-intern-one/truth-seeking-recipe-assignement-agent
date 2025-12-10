import os
from dataclasses import dataclass
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import redis.asyncio as redis
import httpx
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class AgentDependencies:
    """Dependencies injected into PydanticAI agents"""
    mongo_db: AsyncIOMotorDatabase
    redis_client: redis.Redis
    http_client: httpx.AsyncClient
    
    # Context for current operation
    recipe_id: Optional[str] = None
    user_context: Optional[dict] = None


async def get_dependencies() -> AgentDependencies:
    """
    Factory function to create dependencies.
    Uses environment variables from .env file for configuration.
    """
    # Get configuration from environment (same as our extensions)
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "recipe_crawler")
    REDIS_URL = os.getenv("REDIS_URL")
    
    # Create async MongoDB client
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    
    # Create async Redis client
    redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
    
    # Create HTTP client for external requests
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
    Should be called when shutting down.
    """
    await deps.http_client.aclose()
    await deps.redis_client.close()
    # Motor client closes automatically