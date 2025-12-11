import os
import asyncio
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tavily import TavilyClient
from pydantic_ai import RunContext

class ParallelWebSearchTool:
    """Optimized web search tool using ThreadPoolExecutor for true parallel execution."""
    
    def __init__(self, max_results=10, max_workers=20):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY must be set")
        self.client = TavilyClient(api_key=api_key)
        self.max_results = max_results
        self.max_workers = max_workers
        self._cache = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def _search_sync(self, query: str) -> Dict[str, Any]:
        """Execute a single search synchronously (runs in thread pool)."""
        # Check cache first (thread-safe for reads)
        cache_key = query.lower().strip()
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            resp = self.client.search(
                query,
                max_results=self.max_results,
                include_answer=True,
                search_depth="basic"  # Faster than "advanced"
            )
            self._cache[cache_key] = resp
            return resp
        except Exception as e:
            return {"error": f"Search failed for '{query}': {str(e)}", "results": []}

    async def _search_single(self, query: str) -> Dict[str, Any]:
        """Execute a single search asynchronously using thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._search_sync, query)

    async def search_parallel(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Execute multiple searches in parallel using ThreadPoolExecutor.
        
        Args:
            queries: List of search query strings
            
        Returns:
            List of search results in the same order as queries
        """
        if not queries:
            return []
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        query_indices = {}  # Map original indices
        
        for i, q in enumerate(queries):
            q_normalized = q.lower().strip()
            if q_normalized not in seen:
                seen.add(q_normalized)
                unique_queries.append(q)
                query_indices[q] = i
        
        # Submit all searches to thread pool simultaneously
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(self._executor, self._search_sync, q)
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
        """
        Single search interface for backward compatibility.
        
        Args:
            ctx: The PydanticAI run context
            query: The search query to execute
        """
        return await self._search_single(query)

    def clear_cache(self):
        """Clear the search cache."""
        self._cache.clear()
    
    def __del__(self):
        """Cleanup thread pool on deletion."""
        self._executor.shutdown(wait=False)


class BatchWebSearchTool:
    """Tool for batching multiple searches with ThreadPoolExecutor."""
    
    def __init__(self, max_results=10, max_workers=20):
        self.parallel_tool = ParallelWebSearchTool(
            max_results=max_results,
            max_workers=max_workers
        )
    
    async def __call__(self, ctx: RunContext, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Execute multiple web searches in parallel using thread pool.
        
        Args:
            ctx: The PydanticAI run context
            queries: List of search queries to execute in parallel
            
        Returns:
            List of search results, one per query
        """
        return await self.parallel_tool.search_parallel(queries)


class OptimizedBatchSearchTool:
    """Advanced batch search with query optimization and thread pooling."""
    
    def __init__(self, max_results=10, max_workers=20):
        self.client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        self.max_results = max_results
        self.max_workers = max_workers
        self._cache = {}
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def _optimize_query(self, query: str) -> str:
        """Optimize query for faster search (3-5 keywords)."""
        words = query.split()
        if len(words) > 5:
            # Keep first 5 words (simple heuristic)
            return ' '.join(words[:5])
        return query
    
    def _batch_search_sync(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Execute all searches synchronously in this thread."""
        results = []
        for query in queries:
            cache_key = query.lower().strip()
            
            # Check cache
            if cache_key in self._cache:
                results.append(self._cache[cache_key])
                continue
            
            # Execute search
            try:
                resp = self.client.search(
                    query,
                    max_results=self.max_results,
                    include_answer=True,
                    search_depth="basic"
                )
                self._cache[cache_key] = resp
                results.append(resp)
            except Exception as e:
                results.append({
                    "error": f"Search failed for '{query}': {str(e)}",
                    "results": []
                })
        
        return results
    
    async def __call__(
        self, 
        ctx: RunContext, 
        queries: List[str],
        optimize: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute optimized batch searches using thread pool.
        
        Args:
            ctx: The PydanticAI run context
            queries: List of search queries
            optimize: Auto-optimize queries for speed
            
        Returns:
            List of search results
        """
        if not queries:
            return []
        
        # Optimize queries if requested
        if optimize:
            queries = [self._optimize_query(q) for q in queries]
        
        # Remove duplicates
        seen = set()
        unique_queries = []
        for q in queries:
            q_normalized = q.lower().strip()
            if q_normalized not in seen:
                seen.add(q_normalized)
                unique_queries.append(q)
        
        # Split queries into batches for parallel processing
        # Each thread handles a batch
        batch_size = max(1, len(unique_queries) // self.max_workers)
        batches = [
            unique_queries[i:i + batch_size]
            for i in range(0, len(unique_queries), batch_size)
        ]
        
        # Execute batches in parallel threads
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(self._executor, self._batch_search_sync, batch)
            for batch in batches
        ]
        
        # Gather all results
        batch_results = await asyncio.gather(*futures, return_exceptions=True)
        
        # Flatten results
        all_results = []
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                all_results.append({
                    "error": f"Batch search failed: {str(batch_result)}",
                    "results": []
                })
            else:
                all_results.extend(batch_result)
        
        return all_results
    
    def __del__(self):
        """Cleanup thread pool."""
        self._executor.shutdown(wait=False)