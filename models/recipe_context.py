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
    tfidf: float | None = Field(None, description="TF-IDF score (deprecated)")
    contains_notes_in_content: bool | None = Field(None, description="Content validation (deprecated)")


class EvidenceQuery(BaseModel):
    query: str = Field(..., description="The exact search query used")
    evidence_items: List[Evidence] = Field(
        ..., description="List of evidence items found"
    )


class UserScenario(BaseModel):
    scenario: str = Field(..., description="User scenario text")


class UserDetails(BaseModel):
    height: float = Field(..., description="Height in cm or meters")
    weight: float = Field(..., description="Weight in kg")
    age: int = Field(..., description="Age in years")
    lifestyle: Lifestyle = Field(..., description="User lifestyle enum")


class RecipeContext(BaseModel):
    meal_id: str = Field(
        ..., description="ID of the meal this context belongs to (MongoDB _id)"
    )
    title: str = Field(..., description="Recipe title")
    evidence: List[EvidenceQuery] = Field(default_factory=list)
    user_scenarios: List[UserScenario] = Field(default_factory=list)
    user_details: List[UserDetails] = Field(default_factory=list)
