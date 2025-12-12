import asyncio
from agents.truth_seeking_agent import optimized_tool

async def test():
    results = await optimized_tool(None, ['salmon omega-3', 'low GI fish', 'protein diabetes'], optimize=True)
    print(f'✓ optimized_search works: {len(results)} results')

asyncio.run(test())
