import os
import asyncio
from typing import List
from pydantic_ai import Agent, RunContext
from deps.dependencies import get_dependencies, AgentDependencies, cleanup_dependencies
from models.recipe_context import Evidence
from prompts.agent import AgentPrompt
from tools.web_search_tool import (
    ParallelWebSearchTool,
    OptimizedBatchSearchTool
)
import logfire


logfire.configure()
logfire.instrument_pydantic_ai()

SYSTEM_PROMPT = AgentPrompt.system_prompt + """

EFFICIENCY RULES:
- Use optimized_search for multiple queries (TRUE parallel execution with auto-optimization)
- Keep queries concise (3-5 keywords)
- Batch related searches together
"""

truth_agent = Agent(
    "groq:moonshotai/kimi-k2-instruct-0905",
    deps_type=AgentDependencies,    
    system_prompt=SYSTEM_PROMPT,
    retries=1,
)



optimized_tool = OptimizedBatchSearchTool(
    max_results=10,
    max_workers=20
)




@truth_agent.tool
async def optimized_search(
    ctx: RunContext[AgentDependencies],
    queries: List[str]
) -> List[dict]:
    """
    MOST EFFICIENT parallel search with auto-optimization and batching.
    Automatically optimizes queries and distributes across thread pool.
    
    Args:
        queries: List of search queries (will be auto-optimized)
        
    Returns:
        List of optimized search results
    """
    return await optimized_tool(ctx, queries, optimize=True)

    """Benchmark different search methods."""
    deps = await get_dependencies()
    
    test_queries = [
        "salmon omega-3 diabetes",
        "low glycemic index fish",
        "protein blood sugar control",
        "healthy fats diabetes diet"
    ]
    
    print("\n" + "="*60)
    print("BENCHMARKING SEARCH METHODS")
    print("="*60)
    
    # Test 1: Sequential (simulated)
    print("\n1. Sequential Search (baseline):")
    print(f"   Estimated time: ~{len(test_queries) * 1.5:.1f}s (1.5s per query)")
    
    # Test 2: Batch with ThreadPoolExecutor
    print("\n2. Batch Search (ThreadPoolExecutor):")
    start = asyncio.get_event_loop().time()
    results = await batch_tool.parallel_tool.search_parallel(test_queries)
    elapsed = asyncio.get_event_loop().time() - start
    print(f"   Actual time: {elapsed:.2f}s")
    print(f"   Speedup: {(len(test_queries) * 1.5) / elapsed:.1f}x faster")
    
    # Test 3: Optimized batch
    print("\n3. Optimized Batch Search:")
    start = asyncio.get_event_loop().time()
    results = await optimized_tool(None, test_queries, optimize=True)
    elapsed = asyncio.get_event_loop().time() - start
    print(f"   Actual time: {elapsed:.2f}s")
    print(f"   Speedup: {(len(test_queries) * 1.5) / elapsed:.1f}x faster")
    
    print("\n" + "="*60 + "\n")

async def analyze_recipe(recipe_text: str) -> str:
    """
    Analyze a recipe using the truth seeking agent.
    
    Args:
        recipe_text: The full text of the recipe and user context.
        
    Returns:
        The JSON analysis result string.
    """
    deps = await get_dependencies()
    try:
        result = await truth_agent.run(recipe_text, deps=deps)
        return result.output
    finally:
        await cleanup_dependencies(deps)

async def main():
    # Only import cleanup if running as script to avoid circular import issues if implemented elsewhere
    # But since we have cleanup_dependencies in deps, we can use it.
    from deps.dependencies import  cleanup_dependencies 
    
    recipe_text = """
Title: Baked Lemon Herb Salmon

Description: A healthy and flavorful salmon recipe, packed with protein and omega-3 fatty acids.

Cook Time: 25 min

Ingredients:
- 4 salmon fillets (about 150g each)
- 2 tbsp olive oil
- 1 lemon, thinly sliced
- 3 cloves garlic, minced
- 1 tsp dried thyme
- 1 tsp dried rosemary
- Salt and pepper to taste
- Fresh parsley for garnish

Preparation Steps:
1. Preheat oven to 200°C (400°F). Line a baking tray with parchment paper.
2. Place salmon fillets on the tray. Drizzle with olive oil and sprinkle garlic, thyme, rosemary, salt, and pepper evenly over the fillets.
3. Lay lemon slices on top of each fillet.
4. Bake for 12-15 minutes, or until the salmon flakes easily with a fork.
5. Garnish with fresh parsley and serve with steamed vegetables or a side salad.

Nutrition (per serving): Calories: 280, Protein: 25g, Carbs: 2g, Fat: 18g
"""  
    
    print("Starting analysis with ThreadPoolExecutor...")
    start_time = asyncio.get_event_loop().time()
    
    # Construct the full prompt context for the test
    full_prompt = f"Based on this recipe, explain why it is suitable for someone with diabetes.\n\n{recipe_text}"
    
    output = await analyze_recipe(full_prompt)
    
    end_time = asyncio.get_event_loop().time()
    elapsed = end_time - start_time
    
    print(f"\n{'='*60}")
    print(f"⚡ EXECUTION TIME: {elapsed:.2f} seconds")
    print(f"{'='*60}\n")
    print(output)


if __name__ == "__main__":
    asyncio.run(main())