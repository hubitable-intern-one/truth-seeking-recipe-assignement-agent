import os
import asyncio
import json
import traceback
from extensions.mongo import meals_collection, recipe_contexts_collection
from agents.truth_seeking_agent import analyze_recipe

def process_meal(meal_id: str):
    """
    Process a single meal:
    - Fetch meal from MongoDB
    - Format structured text for the agent
    - Call the async analyze_recipe agent
    - Save the parsed evidence back to MongoDB
    """
    print(f"Processing meal: {meal_id}")

    try:
        # 1. Fetch meal from MongoDB
        meal = meals_collection.find_one({"_id": meal_id})
        if not meal:
            print(f"Meal not found: {meal_id}")
            return

        # 2. Format structured text for the agent
        recipe_text = f"Title: {meal.get('title', 'Unknown')}\n"
        recipe_text += f"Type: {meal.get('type', 'Unknown')}\n"
        recipe_text += f"Description: {meal.get('description', '')}\n"
        recipe_text += f"Prep Time: {meal.get('prep_time', '')}\n"
        recipe_text += f"Cook Time: {meal.get('cook_time', '')}\n"
        recipe_text += f"Cuisine Style: {meal.get('cuisine_style', '')}\n"
        recipe_text += f"Image URL: {meal.get('image_url', '')}\n\n"

        # Ingredients
        ingredients = meal.get('ingredients', [])
        ing_text = ""
        if isinstance(ingredients, list):
            for ing in ingredients:
                item = ing.get('item', 'Unknown')
                portion = ing.get('portion', '')
                ing_text += f"- {{'item': '{item}', 'portion': '{portion}'}}\n"
        recipe_text += f"Ingredients:\n{ing_text}\n"

        # Preparation Steps
        prep_steps = meal.get('preparation_steps', [])
        step_text = ""
        if isinstance(prep_steps, list):
            for step in prep_steps:
                s = step.get('step', '')
                desc = step.get('description', '')
                # Only include description if present
                step_text += f"- {{'step': '{s}', 'description': '{desc}'}}\n"
        recipe_text += f"Preparation Steps:\n{step_text}\n"

        # Nutrition
        nutrition = meal.get('nutrition', {})
        nutrition_text = ""
        if nutrition:
            for key in ['calories', 'protein', 'carbs', 'fat']:
                val = nutrition.get(key, None)
                if val is not None:
                    nutrition_text += f"- {key.capitalize()}: {val}\n"
        recipe_text += f"Nutrition:\n{nutrition_text}\n"

        # Allergens
        allergens = meal.get('allergens', None)
        if not allergens:
            allergens = None
        recipe_text += f"Allergens: {allergens}\n"

        # Why this meal
        why_this_meal = meal.get('why_this_meal', [])
        if not why_this_meal:
            why_this_meal = []
        why_text = ", ".join(why_this_meal) if why_this_meal else "None"
        recipe_text += f"Why This Meal: {why_text}\n"

        # Add default query wrapper
        full_query = f"Based on this recipe, please perform evidence collection.\n\n{recipe_text}"

        # 3. Call Agent (async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        json_output = loop.run_until_complete(analyze_recipe(full_query))
        loop.close()

        if not json_output:
            print(f"No output from agent for meal {meal_id}")
            return

        # 4. Parse agent output
        try:
            parsed_data = json.loads(json_output)
        except json.JSONDecodeError:
            print(f"Failed to parse agent output for meal {meal_id}: {json_output}")
            return

        # 5. Save to recipe_contexts collection
        recipe_contexts_collection.update_one(
            {"meal_id": meal_id},
            {
                "$set": {
                    "meal_id": meal_id,
                    "title": meal.get('title'),
                    "evidence": parsed_data,
                    "updated_at": os.popen('date -u +"%Y-%m-%dT%H:%M:%SZ"').read().strip()
                }
            },
            upsert=True
        )

        print(f"Successfully processed and saved meal {meal_id}")

    except Exception as e:
        traceback.print_exc()
        print(f"Failed to process meal {meal_id}: {str(e)}")
