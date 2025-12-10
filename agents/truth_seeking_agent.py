from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from typing import List
import httpx

from models.recipe_context import Evidence, EvidenceStatus
from deps.dependencies import AgentDependencies


class EvidenceValidation(BaseModel):
    """Structured output for evidence validation"""
    is_valid: bool = Field(..., description="Whether evidence is credible and relevant")
    status: EvidenceStatus = Field(..., description="Validation status")
    reasoning: str = Field(..., description="Detailed reasoning for the decision")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in validation")
    required_actions: List[str] = Field(
        default_factory=list,
        description="Actions needed if more validation required"
    )


# Initialize PydanticAI agent
truth_seeking_agent = Agent(
    'huggingface:Qwen/Qwen3-235B-A22B',
    result_type=EvidenceValidation,
    system_prompt="""You are a truth-seeking agent that validates evidence for recipe assignments.

Your role is to:
1. Assess whether evidence credibly supports assigning a recipe to a specific user scenario
2. Check if evidence is from reliable sources (medical journals, nutrition databases, etc.)
3. Verify that evidence is relevant to the user's specific situation
4. Apply Theory of Mind: Consider if this recipe would truly help this specific user

Be skeptical but fair. Consider:
- Is the source authoritative?
- Does the evidence directly address the user's scenario?
- Are there any safety concerns or contraindications?
- Would a reasonable nutritionist recommend this?

Prioritize user safety and evidence quality over being permissive."""
)


@truth_seeking_agent.tool
async def check_url_status(ctx: RunContext[AgentDependencies], url: str) -> dict:
    """Check if a URL is accessible and returns valid content"""
    try:
        response = await ctx.deps.http_client.get(url, follow_redirects=True)
        return {
            "accessible": response.status_code == 200,
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type", "unknown"),
            "content_length": len(response.content)
        }
    except Exception as e:
        return {
            "accessible": False,
            "error": str(e)
        }


@truth_seeking_agent.tool
async def search_keywords_in_content(
    ctx: RunContext[AgentDependencies], 
    url: str, 
    keywords: List[str]
) -> dict:
    """Search for specific keywords in webpage content"""
    try:
        response = await ctx.deps.http_client.get(url)
        content = response.text.lower()
        
        found_keywords = [kw for kw in keywords if kw.lower() in content]
        
        return {
            "found": len(found_keywords) > 0,
            "matched_keywords": found_keywords,
            "match_percentage": len(found_keywords) / len(keywords) if keywords else 0
        }
    except Exception as e:
        return {
            "found": False,
            "error": str(e)
        }


async def validate_evidence(
    evidence: Evidence,
    user_scenario: str,
    deps: AgentDependencies
) -> Evidence:
    """
    Validate a single piece of evidence using the truth-seeking agent
    
    Args:
        evidence: Evidence to validate
        user_scenario: User's dietary scenario/goal
        deps: Agent dependencies
    
    Returns:
        Updated evidence with validation results
    """
    
    # Run the agent
    result = await truth_seeking_agent.run(
        f"""Validate this evidence for the given user scenario.

USER SCENARIO: {user_scenario}

EVIDENCE:
Notes: {evidence.notes}
Source: {evidence.source_link}

Assess whether this evidence credibly supports assigning a recipe to this user.""",
        deps=deps
    )
    
    # Update evidence with validation results
    validation: EvidenceValidation = result.data
    evidence.validation_status = validation.status
    evidence.validation_reasoning = validation.reasoning
    
    return evidence