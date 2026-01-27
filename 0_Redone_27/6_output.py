import asyncio
import json
from agents.truth_seeking_agent import analyze_recipe
from config.synthetic_users import TEST_PROFILES

async def main():
    # 1. Define the recipe text
    recipe_text = """
    Title: Salty Bacon Bomb Burger
    Ingredients: 
    - 500g Ground Beef (20% Fat)
    - 10 strips Bacon (Fried)
    - 2 tbsp Salt
    - 3 slices American Cheese
    - 1 Brioche Bun
    """

    print(f"🚀 Analyzing for {len(TEST_PROFILES)} specific users...")

    try:
        # 2. Run the Analysis
        result = await analyze_recipe(recipe_text, user_profiles=TEST_PROFILES)

        print(f"\n✅ Analysis Complete for: {result.title}")
        
        # 3. Print Summary (Human Readable)
        print("\n--- 🩺 VERDICT SUMMARY ---")
        for scenario in result.user_scenario:
            print(f"[{scenario.verdict}] {scenario.scenario}")

        # 4. DUMP FULL JSON (Machine Readable)
        print("\n" + "="*60)
        print("📂 FULL RAW JSON OUTPUT")
        print("="*60)
        
        # Pydantic has a built-in helper for this
        # indent=2 makes it readable in the terminal
        print(result.model_dump_json(indent=2))
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())