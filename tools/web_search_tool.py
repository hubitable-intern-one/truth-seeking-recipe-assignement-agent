import os
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from tavily import TavilyClient
from pydantic_ai import RunContext
from tools.ranking_tool import RankingTool


class ParallelWebSearchTool:
    """Optimized web search tool with parallel ranking."""
    
    def __init__(self, max_results=10, max_workers=20):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY must be set")
        self.client = TavilyClient(api_key=api_key)
        self.max_results = max_results
        self.max_workers = max_workers
        self._cache = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self.ranker = RankingTool()

    def _search_and_rank_sync(self, query: str) -> Dict[str, Any]:
        """Execute search AND ranking in a single thread (avoids context switching)."""
        cache_key = query.lower().strip()
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # Search
            resp = self.client.search(
                query,
                max_results=self.max_results,
                include_answer=False,
                search_depth="basic"
            )
            
            # Extract results
            results = [
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "content": r.get("content")
                }
                for r in resp.get("results", [])
            ]
            
            # Rank immediately (in same thread)
            ranked_results = self.ranker.rank_results(query, results, top_k=5)
            
            filtered = {"results": ranked_results}
            self._cache[cache_key] = filtered
            return filtered
            
        except Exception as e:
            return {"error": f"Search failed for '{query}': {str(e)}", "results": []}

    async def search_parallel(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute multiple searches + rankings in parallel."""
        if not queries:
            return []
        
        # Deduplicate
        seen = set()
        unique_queries = []
        for q in queries:
            q_normalized = q.lower().strip()
            if q_normalized not in seen:
                seen.add(q_normalized)
                unique_queries.append(q)
        
        # Submit all search+rank operations in parallel
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(self._executor, self._search_and_rank_sync, q)
            for q in unique_queries
        ]
        
        # Wait for all to complete
        results = await asyncio.gather(*futures, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "error": f"Search failed for '{unique_queries[i]}': {str(result)}",
                    "results": []
                })
            else:
                processed_results.append(result)
        
        return processed_results

    async def __call__(self, ctx: RunContext, query: str) -> Dict[str, Any]:
        """Single search interface."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._search_and_rank_sync, query)

    def clear_cache(self):
        """Clear the search cache."""
        self._cache.clear()
    
    def __del__(self):
        """Cleanup thread pool on deletion."""
        self._executor.shutdown(wait=False)





class OptimizedBatchSearchTool:
    """Advanced batch search with parallel ranking."""
    
    def __init__(self, max_results=10, max_workers=20):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY must be set")
        self.client = TavilyClient(api_key=api_key)
        self.max_results = max_results
        self.max_workers = max_workers
        self._cache = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self.ranker = RankingTool()
    
    def _optimize_query(self, query: str) -> str:
        """Optimize query for faster search (3-5 keywords)."""
        words = query.split()
        if len(words) > 5:
            return ' '.join(words[:5])
        return query
    
    def _search_and_rank_batch_sync(
        self, 
        queries_with_indices: List[tuple[int, str]]
    ) -> List[tuple[int, Dict[str, Any]]]:
        """
        Execute batch of searches+rankings in a single thread.
        Returns list of (original_index, result) tuples for correct ordering.
        """
        results = []
        
        for idx, query in queries_with_indices:
            cache_key = query.lower().strip()
            
            if cache_key in self._cache:
                results.append((idx, self._cache[cache_key]))
                continue
            
            try:
                resp = self.client.search(
                    query,
                    max_results=self.max_results,
                    include_answer=False,
                    search_depth="basic"
                )
                
                raw_results = [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "content": r.get("content")
                    }
                    for r in resp.get("results", [])
                ]
                
                
                ranked = self.ranker.rank_results(query, raw_results, top_k=5)
                filtered = {"results": ranked}
                
                self._cache[cache_key] = filtered
                results.append((idx, filtered))
                
            except Exception as e:
                results.append((idx, {
                    "error": f"Search failed for '{query}': {str(e)}",
                    "results": []
                }))
        
        return results
    
    async def __call__(
        self, 
        ctx: RunContext, 
        queries: List[str],
        optimize: bool = True
    ) -> List[Dict[str, Any]]:
        """Execute optimized batch searches with parallel ranking."""
        if not queries:
            return []
        
        # Optimize queries
        if optimize:
            queries = [self._optimize_query(q) for q in queries]
        
        # Deduplicate while preserving order mapping
        seen = set()
        unique_queries_with_idx = []
        for i, q in enumerate(queries):
            q_normalized = q.lower().strip()
            if q_normalized not in seen:
                seen.add(q_normalized)
                unique_queries_with_idx.append((i, q))
        
        # Split into batches for parallel processing
        batch_size = max(1, len(unique_queries_with_idx) // self.max_workers)
        batches = [
            unique_queries_with_idx[i:i + batch_size]
            for i in range(0, len(unique_queries_with_idx), batch_size)
        ]
        
        # Execute batches in parallel
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(
                self._executor, 
                self._search_and_rank_batch_sync, 
                batch
            )
            for batch in batches
        ]
        
        # Gather results
        batch_results = await asyncio.gather(*futures, return_exceptions=True)
        
        # Flatten and sort by original index
        all_results_with_idx = []
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                continue  # Skip failed batches
            all_results_with_idx.extend(batch_result)
        
        # Sort by original index to maintain order
        all_results_with_idx.sort(key=lambda x: x[0])
        
        # Return just the results (strip indices)
        return [result for _, result in all_results_with_idx]
    
    def __del__(self):
        """Cleanup thread pool."""
        self._executor.shutdown(wait=False)