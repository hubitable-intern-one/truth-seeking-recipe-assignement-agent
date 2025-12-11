from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class QueryStatus(str, Enum):
    """Status of a query node"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SegmentedQuery(BaseModel):
    """A single query node in the tree"""
    id: str = Field(..., description="Unique identifier for this query")
    query: str = Field(..., description="The actual search query")
    dependencies: List[str] = Field(
        default_factory=list, 
        description="List of query IDs that must complete before this one"
    )
    status: QueryStatus = Field(default=QueryStatus.PENDING)
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class QueryTree(BaseModel):
    """Complete query tree structure"""
    queries: List[SegmentedQuery] = Field(..., description="All queries in the tree")
    
    def get_query(self, query_id: str) -> Optional[SegmentedQuery]:
        """Get a query by ID"""
        return next((q for q in self.queries if q.id == query_id), None)
    
    def get_ready_queries(self) -> List[SegmentedQuery]:
        """Get all queries whose dependencies are satisfied"""
        ready = []
        for query in self.queries:
            if query.status != QueryStatus.PENDING:
                continue
                
            # Check if all dependencies are completed
            deps_completed = all(
                self.get_query(dep_id).status == QueryStatus.COMPLETED
                for dep_id in query.dependencies
            )
            
            if deps_completed or not query.dependencies:
                ready.append(query)
        
        return ready
    
    def is_complete(self) -> bool:
        """Check if all queries are completed"""
        return all(q.status == QueryStatus.COMPLETED for q in self.queries)
    
    def get_dependency_results(self, query: SegmentedQuery) -> Dict[str, Any]:
        """Get results from all dependencies of a query"""
        results = {}
        for dep_id in query.dependencies:
            dep_query = self.get_query(dep_id)
            if dep_query and dep_query.results:
                results[dep_id] = dep_query.results
        return results


async def execute_query_tree(
    tree: QueryTree,
    search_function,  # Function to execute searches
    max_concurrent: int = 3
) -> QueryTree:
    """
    Execute a query tree, respecting dependencies
    
    Args:
        tree: The query tree to execute
        search_function: Async function to execute individual searches
        max_concurrent: Maximum number of concurrent queries
    
    Returns:
        Completed query tree with results
    """
    import asyncio
    
    while not tree.is_complete():
        # Get queries that are ready to run
        ready_queries = tree.get_ready_queries()
        
        if not ready_queries:
            # No queries ready but tree not complete = circular dependency or error
            break
        
        # Execute ready queries (up to max_concurrent at a time)
        tasks = []
        for query in ready_queries[:max_concurrent]:
            query.status = QueryStatus.IN_PROGRESS
            tasks.append(_execute_single_query(query, tree, search_function))
        
        # Wait for batch to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    return tree


async def _execute_single_query(
    query: SegmentedQuery,
    tree: QueryTree,
    search_function
) -> None:
    """Execute a single query with context from dependencies"""
    try:
        # Get context from dependencies
        dep_results = tree.get_dependency_results(query)
        
        # Build enhanced query with context
        context = ""
        if dep_results:
            context = "\n\nContext from previous searches:\n"
            for dep_id, results in dep_results.items():
                context += f"- {dep_id}: {results.get('summary', 'No summary')}\n"
        
        enhanced_query = query.query + context
        
        # Execute search
        results = await search_function(enhanced_query)
        
        query.results = results
        query.status = QueryStatus.COMPLETED
        
    except Exception as e:
        query.status = QueryStatus.FAILED
        query.error = str(e)