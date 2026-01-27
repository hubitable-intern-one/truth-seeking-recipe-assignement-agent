import os
import re
import json
import logfire
from dotenv import load_dotenv
from typing import List, Any, Optional, Dict
from pydantic_ai import Agent, RunContext
from dependencies import get_dependencies, AgentDependencies, cleanup_dependencies
from models.recipe_context import RecipeContext, UserDetails
from config.synthetic_users import TEST_PROFILES
from tools.web_search_tool import OptimizedBatchSearchTool
from tools.verifier_tool import FactVerifier

# --- 1. CONFIGURATION ---
load_dotenv()

# [SAFETY CONTROL]
SEARCH_MAX_RESULTS = 5  
SEARCH_MAX_WORKERS = 20
MODEL_NAME = "groq:llama-3.3-70b-versatile"

# --- 2. LOGFIRE AUTHENTICATION ---
token = os.getenv("LOGFIRE_TOKEN")
if token and token.startswith("logfire_"):
    logfire.configure(service_name="hubitable-agent", token=token)
    logfire.instrument_pydantic()
else:
    logfire.configure(service_name="hubitable-agent", send_to_logfire=False)

# --- 3. AGENT INITIALIZATION ---
truth_agent = Agent(
    MODEL_NAME,
    deps_type=AgentDependencies,    
    retries=2
)

# Initialize Tools
search_tool = OptimizedBatchSearchTool(max_results=SEARCH_MAX_RESULTS, max_workers=SEARCH_MAX_WORKERS)
verifier_tool = FactVerifier()

# --- 4. DYNAMIC SYSTEM PROMPT (RADICALLY SIMPLIFIED) ---
@truth_agent.system_prompt
def add_clinical_context(ctx: RunContext[AgentDependencies]) -> str:
    # Get profiles safely
    current_profiles = getattr(ctx.deps, 'profiles', TEST_PROFILES)
    
    profiles_text = "\n".join([
        f"- {p.label}: {p.age}yo, {p.weight}kg. Cond: {', '.join(p.conditions)}"
        for p in current_profiles
    ])

    return f"""
You are an expert Clinical Dietitian.

Your Objective:
Analyze the provided recipe against these specific patient profiles:
{profiles_text}

Instructions:
1. Search for clinical evidence regarding the recipe's ingredients and the patients' conditions.
2. Consolidate your searches (e.g., search for the full meal profile rather than individual ingredients).
3. Determine a verdict ("Recommended", "Caution", "Avoid") for EACH profile.
4. If the input is gibberish, return health_score: 0.

Output Format:
Return ONLY a VALID JSON object matching this schema.

{{
  "user_scenario": [ 
    {{ "scenario": "The Renal Patient (Stage 3)", "verdict": "AVOID", "reasoning": "..." }} 
  ],
  "evidence": [ 
    {{ 
      "notes": "High sodium increases hypertension risk...", 
      "source_link": "...", 
      "quote": "...",
      "relevant_scenarios": ["The Renal Patient (Stage 3)"] 
    }} 
  ],
  "scientific_summary": "...",
  "health_score": 50
}}

IMPORTANT:
- In "relevant_scenarios", verify you copy the EXACT label from the profile list (e.g. "The Renal Patient (Stage 3)").
- This allows the UI to filter evidence for that specific user.
"""

# --- 5. TOOL REGISTRATION ---
@truth_agent.tool
async def optimized_search(ctx: RunContext[AgentDependencies], queries: List[str]) -> List[dict]:
    """Search the web for clinical data. (Optimized for Efficiency)"""
    
    # Cap queries at 3 to prevent rate limits
    if len(queries) > 3:
        queries = queries[:3] 
        
    enhanced_queries = [f"{q} clinical data" for q in queries]
    
    with logfire.span("Executing Search Tool", queries=queries):
        return await search_tool.search(enhanced_queries)

# --- 6. MAIN PIPELINE ---
async def analyze_recipe(recipe_text: str, user_profiles: List[UserDetails] = None) -> RecipeContext:
    """The Full Pipeline: Agent -> Search -> Smart Extraction -> Audit"""
    
    deps = await get_dependencies()
    # Inject profiles dynamically
    deps.profiles = user_profiles if user_profiles else TEST_PROFILES
    
    with logfire.span("Analyze Recipe Pipeline", recipe_title=recipe_text.split('\n')[0]):
        try:
            logfire.info("Agent starting analysis", text_preview=recipe_text[:50])
            
            # Step 1: Run the AI
            result = await truth_agent.run(recipe_text, deps=deps)
            
            # Step 2: Extract Content (Robustly)
            raw_content = None
            if hasattr(result, 'data'):
                raw_content = result.data
            
            if not raw_content and hasattr(result, 'new_messages'):
                 msgs = result.new_messages() if callable(result.new_messages) else result.new_messages
                 for msg in reversed(msgs):
                     if hasattr(msg, 'parts'):
                         for part in msg.parts:
                             if hasattr(part, 'content'):
                                 raw_content = part.content
                                 break
                     elif hasattr(msg, 'content') and isinstance(msg.content, str):
                         raw_content = msg.content
                     if raw_content: break
            
            if not raw_content:
                raise ValueError("AI Agent returned empty content.")

            if not isinstance(raw_content, str):
                raw_content = str(raw_content)

            # Step 3: Smart JSON Extraction
            def extract_report_json(text: str) -> Optional[Dict[str, Any]]:
                matches = re.finditer(r"\{.*?\}", text, re.DOTALL)
                candidates = []
                for match in matches:
                    try:
                        obj = json.loads(match.group(0))
                        candidates.append(obj)
                    except:
                        continue
                try:
                    greedy = re.search(r"\{.*\}", text, re.DOTALL)
                    if greedy:
                        candidates.append(json.loads(greedy.group(0)))
                except:
                    pass
                
                required_keys = ["health_score", "scientific_summary", "user_scenario"]
                for obj in reversed(candidates):
                    if all(key in obj for key in required_keys):
                        return obj
                return None

            data_dict = extract_report_json(raw_content)
            
            if not data_dict:
                logfire.error("Model outputted text but no valid report JSON", raw_content=raw_content)
                if "queries" in raw_content:
                     raise ValueError("AI Agent Error: The model outputted tool arguments instead of running the tool. (Try running again)")
                raise ValueError("AI returned text but no valid JSON Report object found.")
                
            try:
                data_dict['title'] = "Analyzed Recipe"  
                data_dict['user_details'] = deps.profiles 
                
                draft_data = RecipeContext.model_validate(data_dict)
                
            except json.JSONDecodeError as e:
                logfire.error("JSON Decode Failed", raw_content=raw_content)
                raise e
            
            # Step 4: The Auditor
            with logfire.span("Verifying Facts"):
                verified_data = await verifier_tool.audit_recipe(draft_data)
            
            logfire.info("Analysis Complete", health_score=verified_data.health_score)
            return verified_data
            
        finally:
            await cleanup_dependencies(deps)