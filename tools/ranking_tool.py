from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import re

class RankingTool:
    """Tool for ranking documents using BM25."""
    
    def __init__(self):
        pass
        
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase and remove non-alphanumeric."""
        text = text.lower()
        # Keep only alphanumeric
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return text.split()
    
    def rank_results(self, query: str, results: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rank search results using BM25.
        
        Args:
            query: The search query.
            results: List of search result dictionaries. Must contain 'content' or 'snippet'.
            top_k: Number of top results to return.
            
        Returns:
            List of top_k ranked results.
        """
        if not results:
            return []
            
        # Prepare corpus
        # Use content if available, otherwise title + url
        corpus = []
        for r in results:
            content = r.get("content") or r.get("title", "") + " " + r.get("url", "")
            corpus.append(self._tokenize(content))
            
        # Tokenize query
        tokenized_query = self._tokenize(query)
        
        # Initialize BM25
        bm25 = BM25Okapi(corpus)
        
        # Get scores
        scores = bm25.get_scores(tokenized_query)
        
        # Zip scores with results
        scored_results = list(zip(results, scores))
        
        # Sort by score descending
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        return [r[0] for r in scored_results[:top_k]]
