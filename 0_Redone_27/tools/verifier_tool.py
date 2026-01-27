import httpx
from bs4 import BeautifulSoup
import re
from models.recipe_context import RecipeContext, Evidence

class FactVerifier:
    """
    The Auditor:
    1. Checks if URLs are alive (link_status).
    2. Downloads text and performs Smart Keyword Matching (link_contains_notes_in_content).
    3. Updates the specific boolean flags required by the spec.
    """
    
    async def _fetch_page_text(self, client: httpx.AsyncClient, url: str) -> str:
        """
        Helper to download and clean text from a URL.
        Returns empty string if link is dead (404/403/500).
        """
        try:
            # We use a real browser User-Agent to avoid getting blocked
            resp = await client.get(url)
            
            # If status is 4xx or 5xx, the link is considered "False" for status
            if resp.status_code >= 400:
                return ""
            
            # Parse HTML
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Kill script, style, nav, footer to reduce noise
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()
                
            text = soup.get_text()
            
            # Clean extra whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
            
            return clean_text.lower()
        except Exception as e:
            # Any connection error (timeout, DNS) counts as a dead link
            return ""

    def _check_relevance(self, notes: str, page_text: str) -> bool:
        """
        Checks if the KEYWORDS from the 'notes' exist in the page text.
        Returns True if > 50% of the significant words are found.
        This prevents the AI from citing a generic homepage for a specific fact.
        """
        # 1. Clean the notes (remove small words like 'the', 'is', 'and')
        stop_words = {"the", "is", "at", "which", "on", "and", "a", "an", "of", "in", "to", "for", "with", "are", "be", "that", "this", "it"}
        
        # Remove punctuation and split
        clean_notes = re.sub(r'[^\w\s]', '', notes.lower())
        note_words = [w for w in clean_notes.split() if w not in stop_words and len(w) > 3]
        
        if not note_words:
            # If note is too short (e.g. "Avoid salt"), we give benefit of doubt if link is alive
            return True 
            
        # 2. Count matches
        match_count = sum(1 for w in note_words if w in page_text)
        
        # 3. Calculate Score
        score = match_count / len(note_words)
        
        # If 50% of the keywords are present, we mark it as verified content
        return score >= 0.5

    async def audit_recipe(self, data: RecipeContext) -> RecipeContext:
        """
        Loops through evidence, updates strict Boolean flags, and filters bad data.
        """
        if not data.evidence:
            return data

        print(f"   ... 🕵️‍♂️ Auditing {len(data.evidence)} sources for Link Status & Content Match...")
        
        valid_evidence = []
        
        # Browser Headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
            for item in data.evidence:
                
                # --- STEP 1: CHECK LINK STATUS ---
                # Checks if the server returns 200 OK
                page_text = await self._fetch_page_text(client, item.source_link)
                
                if not page_text:
                    # Requirement: link_status (boolean)
                    item.link_status = False
                    
                    # If link is dead, it definitely doesn't contain notes
                    item.link_contains_notes_in_content = False 
                    
                    print(f"      ⚠️ DEAD LINK: {item.source_link}")
                    data.warnings.append(f"Dead link found: {item.source_link}")
                    
                    # We continue to the next item (effectively filtering this one out of valid_evidence)
                    # OR if you want to keep dead links in DB to show they failed, append to valid_evidence here.
                    # For now, we usually filter them out to keep the UI clean.
                    continue 
                else:
                    item.link_status = True

                # --- STEP 2: CHECK CONTENT MATCH ---
                # Requirement: link_contains_notes_in_content (boolean)
                is_relevant = self._check_relevance(item.notes, page_text)
                
                item.link_contains_notes_in_content = is_relevant
                
                if is_relevant:
                    # PERFECT MATCH: Status 200 AND Content Verified
                    valid_evidence.append(item)
                else:
                    # Link works, but content is irrelevant/hallucinated
                    print(f"      👻 CONTENT MISMATCH: {item.source_link}")
                    data.warnings.append(f"Source text did not match notes: {item.notes[:30]}...")
                    # We currently filter these out. 
                    # If you want to show "Failed Evidence" in UI, append it to valid_evidence anyway.

        # Update the list to only include compliant evidence
        data.evidence = valid_evidence
        
        return data