import os
import asyncio
import sys
import json
from dotenv import load_dotenv
from extensions.mongo import meals_collection
from agents.truth_seeking_agent import analyze_recipe
from config.synthetic_users import TEST_PROFILES

# Load environment variables
load_dotenv()

async def run_test():
    print("[TEST] DIAGNOSTIC STARTED")
    print("-" * 50)
    
    # 1. Check MongoDB Access
    print("[STEP 1] Checking MongoDB connection...")
    try:
        # Looking for the specific recipe
        meal = meals_collection.find_one({"title": "Cajun Shrimp Pasta"})
        
        if not meal:
            print("   [WARN] Specific recipe not found. Fetching random recipe...")
            meal = meals_collection.find_one()
        
        if not meal:
            print("   [CRITICAL] No recipes found in database.")
            return
        print(f"   [SUCCESS] Recipe Loaded: {meal.get('title')}")
    except Exception as e:
        print(f"   [ERROR] MongoDB connection failed: {e}")
        return

    # 2. Prepare Text
    print("[STEP 2] Formatting recipe text...")
    try:
        # --- A. FORMAT INGREDIENTS ---
        ingredients = meal.get('ingredients', [])
        ing_list = []
        
        if isinstance(ingredients, list):
            for item in ingredients:
                if isinstance(item, str):
                    ing_list.append(item)
                elif isinstance(item, dict):
                    # Unpack 'portion' and 'item'
                    portion = item.get('portion', '').strip()
                    name = item.get('item', '').strip()
                    
                    if portion:
                        full_line = f"- {portion} {name}"
                    else:
                        full_line = f"- {name}"
                    ing_list.append(full_line)
        else:
            ing_list.append(str(ingredients))
        ing_str = '\n'.join(ing_list)

        # --- B. FORMAT INSTRUCTIONS ---
        # Check for 'preparation_steps' first (List of Dicts)
        steps_data = meal.get('preparation_steps', [])
        inst_list = []

        if steps_data and isinstance(steps_data, list):
            for step in steps_data:
                # Format: "1. Mix the ingredients..."
                s_num = step.get('step', '')
                s_desc = step.get('description', '')
                inst_list.append(f"{s_num}. {s_desc}")
            instructions_str = '\n'.join(inst_list)
        else:
            # Fallback to legacy 'instructions' field
            instructions_str = meal.get('instructions', "Mix and cook.")

        # --- C. ASSEMBLE TEXT ---
        recipe_text = f"""
        Title: {meal.get('title')}
        
        Ingredients List:
        {ing_str}
        
        Cooking Instructions:
        {instructions_str}
        """
        
        # Preview
        print("\n   --- INPUT PREVIEW ---")
        print('\n'.join(recipe_text.split('\n')[:10])) # Print first 10 lines
        print("   ---------------------\n")
        
        print("   [SUCCESS] Text formatting complete.")
    except Exception as e:
        print(f"   [ERROR] Formatting failed: {e}")
        return

    # 3. Run Agent
    print("[STEP 3] calling AI Agent (Analysis started)...")
    
    try:
        result = await asyncio.wait_for(analyze_recipe(recipe_text), timeout=180.0)
        
        print("\n" + "="*60)
        print(f"REPORT FOR: {meal.get('title')}")
        print("="*60)
        
        print(f"\nHEALTH SCORE: {result.health_score}/100")
        print(f"\nSCIENTIFIC SUMMARY:\n{result.scientific_summary}")
        
        print("\n" + "-"*60)
        print("PATIENT SCENARIOS")
        print("-" * 60)
        
        if result.user_scenario:
            for i, scenario in enumerate(result.user_scenario, 1):
                print(f"\nSCENARIO {i}: {scenario.scenario}")
                print(f"   Verdict:   {scenario.verdict.upper()}")
                print(f"   Reasoning: {scenario.reasoning}")
        else:
            print("   [WARN] No scenarios returned.")
            
        print("\n" + "-"*60)
        print("VERIFIED EVIDENCE")
        print("-" * 60)
        
        if result.evidence:
            for i, ev in enumerate(result.evidence, 1):
                print(f"\nSOURCE {i}:")
                print(f"   Claim:  {ev.notes}")
                print(f"   Quote:  \"{ev.quote}\"")
                print(f"   Link:   {ev.source_link}")
        else:
            print("   [INFO] No external evidence cited.")

        print("📂 FULL RAW JSON OUTPUT")
        print("="*60)
        
        # Pydantic has a built-in helper for this
        # indent=2 makes it readable in the terminal
        print(result.model_dump_json(indent=2))
        print("="*60 + "\n")

        print("\n" + "="*60)
        print("[TEST] COMPLETE")

    except asyncio.TimeoutError:
        print("\n   [ERROR] TIMEOUT: Agent took too long to respond.")
    except Exception as e:
        print(f"\n   [CRITICAL] AGENT CRASHED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_test())