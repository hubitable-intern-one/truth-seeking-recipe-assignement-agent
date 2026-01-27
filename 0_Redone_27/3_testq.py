
# #! Simple test to see that its working
# import asyncio
# from arq import create_pool
# from worker import get_redis_settings 

# async def main():

#     redis = await create_pool(await get_redis_settings())
    
#     job = await redis.enqueue_job('run_analysis_task', recipe_text="Boil water.")
#     print(f"Job sent! ID: {job.job_id}")

# if __name__ == '__main__':
#     asyncio.run(main())

#! Bigger test using a recipe

import asyncio
from arq import create_pool
from worker import REDIS_SETTINGS # Import settings directly

async def main():
    # 1. Connect to Redis
    redis = await create_pool(REDIS_SETTINGS)
    
    # 2. Define a REAL recipe payload
    real_recipe_text = """
    Title: Classic Beef Burger
    Ingredients:
    - 500g Ground Beef (20% Fat)
    - 1 tsp Salt
    - 1/2 tsp Black Pepper
    - 4 Brioche Buns
    - 2 tbsp Mayonnaise
    - 4 slices American Cheese
    """
    
    print("🚀 Sending REAL recipe job to Redis...")
    
    # 3. Push the job
    job = await redis.enqueue_job(
        'run_analysis_task', 
        recipe_text=real_recipe_text
    )
    
    print(f"✅ Job sent! ID: {job.job_id}")
    print("Check your 'arq worker' terminal now. This should take ~10-15 seconds.")

if __name__ == '__main__':
    asyncio.run(main())