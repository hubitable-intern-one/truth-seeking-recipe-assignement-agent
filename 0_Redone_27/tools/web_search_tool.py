import asyncio
import os
from typing import List, Dict
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# STRICT ACADEMIC SOURCE LIST
# The agent is forbidden from looking anywhere else.
ACADEMIC_SOURCES = [
    "ncbi.nlm.nih.gov",      # PubMed / National Library of Medicine
    "sciencedirect.com",     # Elsevier (Major Journal Repo)
    "nature.com",            # Nature Journal
    "nejm.org",              # New England Journal of Medicine
    "thelancet.com",         # The Lancet
    "jamanetwork.com",       # Journal of American Medical Association
    "bmj.com",               # British Medical Journal
    "wiley.com",             # Wiley Online Library
    "springer.com",          # Springer Journals
    "academic.oup.com",      # Oxford Academic
    "cdc.gov",               # Centers for Disease Control
    "who.int",               # World Health Organization
    "harvard.edu",           # Harvard Health
    "mayoclinic.org",        # Mayo Clinic
    "clevelandclinic.org"    # Cleveland Clinic
]

class OptimizedBatchSearchTool:
    def __init__(self, max_results: int = 5, max_workers: int = 10):
        """
        Args:
            max_results: Number of results per query.
            max_workers: Max parallel threads.
        """
        self.max_results = max_results
        self.semaphore = asyncio.Semaphore(max_workers)
        
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("Missing TAVILY_API_KEY in .env")
            
        self.client = TavilyClient(api_key=api_key)

    async def _search_single(self, query: str) -> List[Dict]:
        """
        Searches for a single query using the Tavily API,
        STRICTLY FILTERED to the Academic Whitelist.
        """
        async with self.semaphore:
            try:
                # We use asyncio.to_thread because the Tavily client is blocking
                response = await asyncio.to_thread(
                    self.client.search,
                    query=query,
                    search_depth="advanced",
                    max_results=self.max_results,
                    include_domains=ACADEMIC_SOURCES  # <--- THE CRITICAL RESTORATION
                )
                return response.get("results", [])
            except Exception as e:
                print(f"⚠️ Search failed for '{query}': {e}")
                return []

    async def search(self, queries: List[str]) -> List[Dict]:
        """
        Runs multiple queries in parallel, flattens the results, and removes duplicates.
        """
        print(f"   ... 🌍 Searching parallel (Academic Only): {queries}")
        
        # 1. Launch all searches simultaneously
        tasks = [self._search_single(q) for q in queries]
        
        # 2. Wait for all to finish
        results_list = await asyncio.gather(*tasks)
        
        # 3. Flatten and Deduplicate
        seen_urls = set()
        unique_results = []
        
        for batch in results_list:
            for item in batch:
                url = item.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append({
                        "url": url,
                        "content": item.get("content"),
                        "title": item.get("title")
                    })
        
        print(f"   ... ✅ Found {len(unique_results)} unique ACADEMIC sources.")
        return unique_results