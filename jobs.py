import os
import asyncio
import json
import traceback
from pymongo import MongoClient
from extensions.mongo import meals_collection, recipe_contexts_collection
from agents.truth_seeking_agent import analyze_recipe

def process_meal(meal_id: str):
    """
    Job function to process a single meal.
    This function is synchronous wrapper properly handling the async agent call.
    """
    print(f"Processing meal: {meal_id}")
    
    try:
        # 1. Fetch meal from MongoDB
        meal = meals_collection.find_one({"_id": meal_id})
        if not meal:
            print(f"Meal not found: {meal_id}")
            return

        # 2. Format context for the agent
        # Assuming meal document has 'title', 'description', 'ingredients', etc.
        # We construct a text representation similar to the prompt example.
        
        recipe_text = f"Title: {meal.get('title', 'Unknown')}\n\n"
        recipe_text += f"Description: {meal.get('description', '')}\n\n"
        
        # Handle ingredients if list or string
        ingredients = meal.get('ingredients', [])
        if isinstance(ingredients, list):
            ing_text = "\n".join([f"- {ing}" for ing in ingredients])
        else:
            ing_text = str(ingredients)
            
        recipe_text += f"Ingredients:\n{ing_text}\n\n"
        recipe_text += f"Preparation Steps:\n{meal.get('method', '')}\n\n" # 'method' or 'instructions'
        
        # Add a default query wrapper if the agent expects it
        full_query = f"Based on this recipe, please perform Phase 1 evidence collection.\n\n{recipe_text}"

        # 3. Call Agent
        # analyze_recipe is async, so we need to run it in an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        json_output = loop.run_until_complete(analyze_recipe(full_query))
        loop.close()
        
        # 4. Parse and Save Result
        # The output is expected to be a JSON string list of evidence queries
        if not json_output:
            print(f"No output from agent for meal {meal_id}")
            return

        try:
            parsed_data = json.loads(json_output)
            
            # Save to recipe_contexts collection
            # Upsert based on meal_id to avoid duplicates
            recipe_contexts_collection.update_one(
                {"meal_id": meal_id},
                {
                    "$set": {
                        "meal_id": meal_id,
                        "title": meal.get('title'),
                        "evidence": parsed_data,
                        "updated_at": os.popen('date -u +"%Y-%m-%dT%H:%M:%SZ"').read().strip() 
                        # Note: os.popen is a quick hack, better use datetime in real app
                    }
                },
                upsert=True
            )
            print(f"Successfully processed and saved meal {meal_id}")
            
        except json.JSONDecodeError:
            print(f"Failed to parse agent output for meal {meal_id}: {json_output}")
            
    except Exception as e:
        print(f"Error processing meal {meal_id}: {str(e)}")
        traceback.print_exc()
