import asyncio
import logging
from datetime import datetime
from bson import ObjectId  # <--- IMPORT THIS

# Import your components
from extensions.mongo import meals_collection, recipe_contexts_collection, failed_jobs_collection
from agents.truth_seeking_agent import analyze_recipe

async def process_meal(meal_id: str):
    print(f"   ... 🍳 Processing Meal ID: {meal_id}")
    
    # 1. Fetch (SAFE ID CONVERSION)
    try:
        # Check if meal_id is already an ObjectId or needs converting
        query_id = ObjectId(meal_id) if ObjectId.is_valid(meal_id) else meal_id
        meal = meals_collection.find_one({"_id": query_id})
    except Exception:
        # Fallback for weird IDs
        meal = meals_collection.find_one({"_id": meal_id})

    if not meal:
        print(f"❌ Error: Meal {meal_id} not found in DB")
        return

    # 2. Format
    # (Safety check: ensure 'ingredients' exists to avoid crashes)
    ingredients_list = meal.get('ingredients', [])
    # Handle cases where ingredients might be strings instead of objects
    if ingredients_list and isinstance(ingredients_list[0], dict):
        ing_text = "\n".join([f"- {i.get('item', '')}" for i in ingredients_list])
    else:
        ing_text = "\n".join([f"- {str(i)}" for i in ingredients_list])

    formatted_text = f"""
    Title: {meal.get('title', 'Unknown Title')}
    Description: {meal.get('description', '')}
    Ingredients:
    {ing_text}
    """

    try:
        # 3. Run AI
        analysis_result = await analyze_recipe(formatted_text)
        
        # 4. Save to MongoDB
        doc_to_save = analysis_result.model_dump()
        doc_to_save['meal_id'] = meal_id  # Save the string ID for easy reading
        doc_to_save['created_at'] = datetime.utcnow()
        
        recipe_contexts_collection.insert_one(doc_to_save)
        print(f"✅ Saved analysis for: {meal.get('title')}")

    except Exception as e:
        print(f"❌ Job Failed for {meal_id}: {e}")
        failed_jobs_collection.insert_one({
            "meal_id": meal_id,
            "error": str(e),
            "timestamp": datetime.utcnow()
        })
        # We do NOT raise e here, so the worker stays alive for the next job