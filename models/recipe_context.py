from pydantic import BaseModel, Field, HttpUrl
from enum import Enum
from typing import List


class Lifestyle(str, Enum):
    SEDENTARY = "sedentary"
    ACTIVE = "active"
    VERY_ACTIVE = "very_active"


class Evidence(BaseModel):
    notes: str = Field(..., description="Notes about the evidence")
    source_link: HttpUrl = Field(..., description="Source link of evidence")
    link_status: bool = Field(..., description="True if link returned 200")
    contains_notes_in_content: bool = Field(
        ..., description="True if notes appear inside page content"
    )


class EvidenceQuery(BaseModel):
    query: str = Field(..., description="The exact search query used")
    evidence_items: List[Evidence] = Field(..., description="List of evidence items found")


class UserScenario(BaseModel):
    scenario: str = Field(..., description="User scenario text")
    

class UserDetails(BaseModel):
    height: float = Field(..., description="Height in cm or meters")
    weight: float = Field(..., description="Weight in kg")
    age: int = Field(..., description="Age in years")
    lifestyle: Lifestyle = Field(..., description="User lifestyle enum")


class RecipeContext(BaseModel):
    title: str = Field(..., description="Recipe title")
    evidence: List[EvidenceQuery] = Field(default_factory=list)
    user_scenarios: List[UserScenario] = Field(default_factory=list)
    user_details: List[UserDetails] = Field(default_factory=list)
