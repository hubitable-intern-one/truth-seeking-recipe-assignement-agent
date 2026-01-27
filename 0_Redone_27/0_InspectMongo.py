import os
from dotenv import load_dotenv
from extensions.mongo import meals_collection
import pprint

# Load Environment
load_dotenv()

def inspect_data():
    print("Full MongoDB Pull")
    
    # 1. Fetch the specific recipe
    query = {"title": "Cajun Shrimp Pasta"}
    meal = meals_collection.find_one(query)
    
    if not meal:
        print("'Cajun Shrimp Pasta' not found")
        return

    #? Metadata
    print("\n" + "="*50)
    print(f"ID: {meal.get('_id')}")
    print(f"TITLE: {meal.get('title')}")
    print(f"TIME: Prep: {meal.get('prep_time')} | Cook: {meal.get('cook_time')}")
    print(f"DESCRIPTION: {meal.get('description')[:100]}...")
    print("="*50)
    
    # ? Precalculated Nutrition
    print(f"\nEXISTING NUTRITION (In DB):")
    pprint.pprint(meal.get('nutrition'))

    #? Print first 3 ingredients
    ingredients = meal.get('ingredients', [])
    print(f"\nINGREDIENTS ({len(ingredients)} items):")
    pprint.pprint(ingredients[:3]) 
    print(f"... and {len(ingredients)-3} more.")

    #? Print instructions
    print(f"Instructions (Steps):")
    steps = meal.get('preparation_steps', [])
    if steps:
        for s in steps:
            print(f"   [{s.get('step')}] {s.get('description')[:60]}...")
    else:
        print("No preparation_steps found.")

if __name__ == "__main__":
    inspect_data()