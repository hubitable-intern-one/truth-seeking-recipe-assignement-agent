import asyncio
import os
import logging
from datetime import datetime
from arq import Worker
from motor.motor_asyncio import AsyncIOMotorClient
from agents.truth_seeking_agent import analyze_recipe

# --- CONFIG ---
REDIS_SETTINGS = {'host': 'localhost', 'port': 6379}
MONGO_URI = os.getenv("MONGO_URI", "mongodb://root:password@localhost:27017")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def startup(ctx):
    """
    Initialize MongoDB connection when the worker starts.
    This connection is shared across all jobs.
    """
    ctx['mongo_client'] = AsyncIOMotorClient(MONGO_URI)
    ctx['db'] = ctx['mongo_client'].recipe_crawler
    logger.info("✅ Worker connected to MongoDB.")

async def shutdown(ctx):
    """Close MongoDB connection when worker stops."""
    if 'mongo_client' in ctx:
        ctx['mongo_client'].close()
    logger.info("🛑 Worker disconnected.")

async def run_analysis_task(ctx, recipe_text: str, recipe_title: str, recipe_id: str):
    """
    The main job. 
    - Success -> Writes to 'new job' collection.
    - Failure -> Writes to 'failed job 2' collection.
    """
    db = ctx['db']
    logger.info(f"🚀 Starting analysis for: {recipe_title} (ID: {recipe_id})")

    try:
        # 1. RUN THE AGENT
        # We set a timeout here to ensure we catch "hanging" agents as failures
        result = await asyncio.wait_for(analyze_recipe(recipe_text), timeout=180.0)

        # 2. PREPARE SUCCESS DATA
        # Convert Pydantic model to a clean dictionary (enums -> strings)
        success_doc = result.model_dump(mode='json')
        
        # Add the tracking metadata you requested
        success_doc['original_recipe_id'] = recipe_id
        success_doc['processed_at'] = datetime.utcnow()
        success_doc['status'] = "success"

        # 3. WRITE TO "new job" COLLECTION
        await db['new job'].insert_one(success_doc)
        logger.info(f"✅ Success! Saved to 'new job': {recipe_title}")
        
        return success_doc

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Job Failed: {error_msg}")

        # 4. PREPARE FAILURE DATA
        fail_doc = {
            "original_recipe_id": recipe_id,
            "recipe_title": recipe_title,
            "recipe_text_snippet": recipe_text[:200], # Save snippet for debugging
            "error": error_msg,
            "failed_at": datetime.utcnow(),
            "status": "failed",
            "retry_count": ctx['job_try'] # arq tracks how many times it tried
        }

        # 5. WRITE TO "failed job 2" COLLECTION
        await db['failed job 2'].insert_one(fail_doc)
        
        # We DO NOT re-raise the exception here. 
        # By catching it and saving to DB, we consider the job "Handled" (as a failure record).
        # If you want ARQ to keep retrying internally, uncomment the next line:
        # raise e 
        return {"status": "failed", "error": error_msg}

# --- ARQ SETTINGS ---
class WorkerSettings:
    functions = [run_analysis_task]
    redis_settings = REDIS_SETTINGS
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10