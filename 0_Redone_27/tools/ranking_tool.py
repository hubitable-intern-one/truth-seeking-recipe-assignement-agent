from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import re

class RankingTool:
    """
    Tool for ranking documents using BM25.
    Acts as a 'Quality Filter' to ensure the AI only reads the most relevant text.
    """
    
    def __init__(self):
        pass
        
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase and remove non-alphanumeric."""
        if not text:
            return []
        text = str(text).lower()
        # Keep only alphanumeric characters to reduce noise
        text = re.sub(r'[^a-z0-9\s]', '', text)
        return text.split()
    
    def rank_results(self, query: str, results: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Rank search results using BM25 algorithm.
        
        Args:
            query: The search query (e.g., "shrimp sodium content").
            results: List of raw search result dictionaries from Tavily.
            top_k: Number of top results to return (default 5).
            
        Returns:
            List of top_k ranked results.
        """
        if not results:
            return []
            
        # 1. Prepare the Corpus (The library of text to search against)
        corpus = []
        valid_results = []

        for r in results:
            # Tavily returns 'content', 'raw_content', or 'snippet'. We grab whatever exists.
            text_content = r.get("content") or r.get("raw_content") or r.get("snippet") or ""
            # Fallback to Title + URL if content is empty
            fallback = r.get("title", "") + " " + r.get("url", "")
            
            # Combine them for the best chance of matching
            full_text = f"{text_content} {fallback}"
            
            tokens = self._tokenize(full_text)
            if tokens:
                corpus.append(tokens)
                valid_results.append(r)
        
        if not corpus:
            return results[:top_k]

        # 2. Tokenize the Query
        tokenized_query = self._tokenize(query)
        
        # 3. Initialize BM25 and Score
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(tokenized_query)
        
        # 4. Sort results by score (highest first)
        # We zip the scores with the valid_results, sort by score descending, and take the top_k
        scored_results = sorted(zip(valid_results, scores), key=lambda x: x[1], reverse=True)
        
        # 5. Extract just the result dictionaries
        top_results = [result for result, score in scored_results[:top_k]]
        
        return top_results