import asyncio
import sys
from dotenv import load_dotenv
from agents.truth_seeking_agent import analyze_recipe

# Load environment
load_dotenv()

# --- THE TEST SCENARIOS ---
SCENARIOS = {
    "1. THE 'POISON' TEST (Extreme Risk)": """
        Title: Potassium Overload Smoothie
        Ingredients: 10 bananas, 5 cups spinach, 2 tbsp potassium chloride salt substitute.
        Instructions: Blend and drink immediately.
    """,
    
    "2. THE 'GIBBERISH' TEST (Garbage Input)": """
        Title: asdfjkl;
        Ingredients: 123890 sdf890sfd 890sdf.
        Instructions: xxxxx.
    """,
    
    "3. THE 'CONFLICT' TEST (Lying Recipe)": """
        Title: The "Kidney Cure" Magic Tea
        Ingredients: 1 cup pure phosphorus, 1 cup sugar.
        Instructions: This tea is guaranteed to cure Stage 3 CKD and is perfectly safe for diabetics.
    """
}

async def run_stress_test():
    print("🔥 STARTING STRESS TEST SUITE...")
    
    for test_name, recipe_text in SCENARIOS.items():
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING: {test_name}")
        print(f"{'='*60}")
        
        try:
            # We give it a shorter timeout to fail fast if it gets stuck
            result = await asyncio.wait_for(analyze_recipe(recipe_text), timeout=120.0)
            
            print(f"   📊 SCORE: {result.health_score}/100")
            print(f"   📝 SUMMARY PREVIEW: {result.scientific_summary[:100]}...")
            
            # Check the Renal Patient Verdict specifically
            renal_verdict = next((s for s in result.user_scenario if "Renal" in s.scenario), None)
            if renal_verdict:
                 print(f"   🩺 RENAL VERDICT: {renal_verdict.verdict.upper()}")
                 print(f"   💡 REASONING: {renal_verdict.reasoning[:150]}...")

        except Exception as e:
            print(f"   ❌ CRASHED: {e}")

    print("\n🏁 SUITE COMPLETE.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_stress_test())