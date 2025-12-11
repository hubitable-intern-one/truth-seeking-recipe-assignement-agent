import os
import asyncio
from typing import List
from pydantic_ai import Agent, RunContext
from deps.dependencies import get_dependencies, AgentDependencies
from models.recipe_context import Evidence
from prompts.agent import AgentPrompt
from tools.web_search_tool import (
    ParallelWebSearchTool, 
    BatchWebSearchTool,
    OptimizedBatchSearchTool
)
import logfire


logfire.configure()
logfire.instrument_pydantic_ai()

SYSTEM_PROMPT = AgentPrompt.system_prompt + """

EFFICIENCY RULES:
- Use batch_web_search or optimized_search for multiple queries (TRUE parallel execution)
- Keep queries concise (3-5 keywords)
- Batch related searches together
"""

truth_agent = Agent(
    "groq:moonshotai/kimi-k2-instruct-0905",
    deps_type=AgentDependencies,    
    system_prompt=SYSTEM_PROMPT,
    retries=1,
)

# Initialize tools with ThreadPoolExecutor (true parallelism)
# max_workers=20 means 20 searches can run simultaneously
parallel_tool = ParallelWebSearchTool(
    max_results=3,
    max_workers=20  # ThreadPoolExecutor with 20 threads
)

batch_tool = BatchWebSearchTool(
    max_results=3,
    max_workers=20
)

optimized_tool = OptimizedBatchSearchTool(
    max_results=3,
    max_workers=20
)

@truth_agent.tool
async def web_search(ctx: RunContext[AgentDependencies], query: str) -> dict:
    """
    Fast single query search using ThreadPoolExecutor.
    
    Args:
        query: Search query (3-5 keywords recommended)
        
    Returns:
        Search results
    """
    return await parallel_tool(ctx, query)

@truth_agent.tool
async def batch_web_search(
    ctx: RunContext[AgentDependencies], 
    queries: List[str]
) -> List[dict]:
    """
    ULTRA-FAST parallel search using ThreadPoolExecutor.
    All queries execute simultaneously in separate threads.
    
    Args:
        queries: List of search queries (3-5 keywords each)
        
    Returns:
        List of results in same order
        
    Example:
        ["salmon diabetes benefits", "omega-3 fatty acids", "low GI fish"]
    """
    return await batch_tool(ctx, queries)

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


async def benchmark_search():
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


async def main():
    deps = await get_dependencies() 
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
    
    result = await truth_agent.run(
        f"Based on this recipe, explain why it is suitable for someone with diabetes.\n\n{recipe_text}",
        deps=deps
    )
    
    end_time = asyncio.get_event_loop().time()
    elapsed = end_time - start_time
    
    print(f"\n{'='*60}")
    print(f"⚡ EXECUTION TIME: {elapsed:.2f} seconds")
    
    if elapsed < 1.0:
        print(f"🚀 EXCELLENT: Sub-1-second performance achieved!")
    elif elapsed < 2.0:
        print(f"✅ GOOD: Under 2 seconds")
    elif elapsed < 3.0:
        print(f"👍 ACCEPTABLE: Under 3 seconds")
    else:
        print(f"⚠️  SLOW: Consider checking network or API performance")
    
    print(f"{'='*60}\n")
    print(result.output)


if __name__ == "__main__":
    # To run benchmark: asyncio.run(benchmark_search())
    asyncio.run(main())