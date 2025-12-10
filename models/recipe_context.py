from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator
from datetime import datetime
from typing import Optional, List, Tuple
from bson import ObjectId
from enum import Enum
import requests


class PyObjectId(ObjectId):
    """Custom ObjectId field for Pydantic."""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if isinstance(value, ObjectId):
            return value
        try:
            return ObjectId(str(value))
        except Exception:
            raise ValueError("Invalid ObjectId")


def verify_url_status(url: str, timeout: float = 3.0) -> Tuple[bool, Optional[str]]:
    """
    Verify that a URL is accessible and returns HTTP 200.
    Optimized for speed using HEAD requests and short timeouts.
    
    Args:
        url: The URL to verify
        timeout: Request timeout in seconds (default: 3.0)
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if URL returns 200, False otherwise
        - error_message: Error description if failed, None if successful
    """
    if not url:
        return False, "No URL provided"
    
    try:
        # Use HEAD request for speed (doesn't download content)
        # Some servers don't support HEAD, so we fallback to GET with streaming
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Try HEAD first (fastest)
        response = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers=headers
        )
        
        # If HEAD not allowed (405) or fails, try GET with streaming
        if response.status_code == 405 or response.status_code >= 400:
            response = requests.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                stream=True,  # Don't download content, just check headers
                headers=headers
            )
            response.close()  # Close immediately after checking status
        
        if response.status_code == 200:
            return True, None
        else:
            return False, f"URL returned status {response.status_code}, expected 200"
            
    except requests.exceptions.Timeout:
        return False, f"URL request timed out after {timeout}s"
    except requests.exceptions.ConnectionError:
        return False, "Failed to connect to URL"
    except requests.exceptions.TooManyRedirects:
        return False, "Too many redirects"
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def verify_keywords_in_content(
    url: str, 
    keywords: List[str], 
    timeout: float = 5.0,
    max_content_length: int = 100000
) -> Tuple[bool, List[str], Optional[str]]:
    """
    Verify that URL content contains specified keywords.
    Optimized for speed with content truncation and streaming.
    
    Args:
        url: The URL to fetch content from
        keywords: List of keywords to search for
        timeout: Request timeout in seconds (default: 5.0)
        max_content_length: Maximum bytes to download (default: 100KB)
        
    Returns:
        Tuple of (contains_all, found_keywords, error_message)
        - contains_all: True if all keywords found, False otherwise
        - found_keywords: List of keywords that were found
        - error_message: Error description if failed, None if successful
    """
    if not url:
        return False, [], "No URL provided"
    
    if not keywords:
        return True, [], None  # No keywords to check
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Use GET with streaming to limit download size
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            stream=True,
            headers=headers
        )
        
        if response.status_code != 200:
            return False, [], f"URL returned status {response.status_code}"
        
        # Check if content is text-based
        content_type = response.headers.get('Content-Type', '')
        if not any(t in content_type.lower() for t in ['text', 'html', 'json', 'xml']):
            response.close()
            return False, [], f"URL does not contain text content (Content-Type: {content_type})"
        
        # Download content in chunks up to max_content_length
        content_bytes = b''
        for chunk in response.iter_content(chunk_size=8192):
            content_bytes += chunk
            if len(content_bytes) >= max_content_length:
                break
        
        response.close()
        
        # Try to decode as UTF-8, fallback to latin-1
        try:
            content_text = content_bytes.decode('utf-8')
        except UnicodeDecodeError:
            content_text = content_bytes.decode('latin-1', errors='ignore')
        
        # Convert to lowercase for case-insensitive matching
        content_lower = content_text.lower()
        
        # Check which keywords are present
        found_keywords = []
        for keyword in keywords:
            if keyword.lower() in content_lower:
                found_keywords.append(keyword)
        
        contains_all = len(found_keywords) == len(keywords)
        
        if contains_all:
            return True, found_keywords, None
        else:
            missing = set(keywords) - set(found_keywords)
            return False, found_keywords, f"Missing keywords: {', '.join(missing)}"
            
    except requests.exceptions.Timeout:
        return False, [], f"Request timed out after {timeout}s"
    except requests.exceptions.ConnectionError:
        return False, [], "Failed to connect to URL"
    except requests.exceptions.RequestException as e:
        return False, [], f"Request failed: {str(e)}"
    except Exception as e:
        return False, [], f"Unexpected error: {str(e)}"


class EvidenceStatus(str, Enum):
    """Validation status for evidence"""
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    NEEDS_MORE_INFO = "needs_more_info"


class Evidence(BaseModel):
    """Evidence supporting recipe assignment to user scenario"""
    notes: str = Field(..., description="Evidence text content")
    source_link: str = Field(..., description="URL source of evidence")
    keywords: Optional[List[str]] = Field(default=None, description="Keywords to verify in source content")
    link_status: Optional[bool] = Field(default=None, description="Whether link is accessible (HTTP 200)")
    contains_keywords: Optional[bool] = Field(default=None, description="Whether source contains expected keywords")
    keywords_found: List[str] = Field(default_factory=list, description="List of keywords found in content")
    validation_status: EvidenceStatus = Field(default=EvidenceStatus.PENDING)
    validation_reasoning: Optional[str] = Field(None, description="AI reasoning for validation decision")
    link_error: Optional[str] = Field(None, description="Error message if link validation failed")
    keyword_error: Optional[str] = Field(None, description="Error message if keyword validation failed")
    
    @field_validator('source_link')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure source_link is a valid URL"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('source_link must be a valid URL')
        return v
    
    @model_validator(mode='after')
    def verify_link_and_keywords(self) -> 'Evidence':
        """Automatically verify link status and keywords if not explicitly set"""
        # Only auto-verify if link_status wasn't explicitly set
        if self.link_status is None:
            is_valid, error_msg = verify_url_status(self.source_link)
            self.link_status = is_valid
            if error_msg:
                self.link_error = error_msg
        
        # Only auto-verify keywords if contains_keywords wasn't explicitly set and keywords provided
        if self.contains_keywords is None and self.keywords:
            # Only check keywords if link_status is True (URL is accessible)
            if self.link_status:
                contains_all, found_kws, error_msg = verify_keywords_in_content(
                    self.source_link, 
                    self.keywords
                )
                self.contains_keywords = contains_all
                self.keywords_found = found_kws
                if error_msg:
                    self.keyword_error = error_msg
            else:
                # Can't check keywords if link is not accessible
                self.contains_keywords = False
                self.keyword_error = "Cannot verify keywords: link is not accessible"
        elif self.contains_keywords is None:
            # No keywords to check
            self.contains_keywords = True
        
        return self


class LifestyleEnum(str, Enum):
    """Lifestyle activity levels"""
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTREMELY_ACTIVE = "extremely_active"


class UserDetails(BaseModel):
    """Physical and lifestyle details of user"""
    age: int = Field(..., ge=0, le=120, description="User age in years")
    weight: float = Field(..., gt=0, description="Weight in kg")
    height: float = Field(..., gt=0, description="Height in cm")
    lifestyle: LifestyleEnum = Field(..., description="Activity level")
    
    def calculate_bmr(self) -> float:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor"""
        # Simplified - assumes average between male/female
        return (10 * self.weight) + (6.25 * self.height) - (5 * self.age) + 5


class UserScenario(BaseModel):
    """A specific user scenario with details"""
    scenario_text: str = Field(..., description="Description of user's dietary goal/situation")
    user_details: UserDetails
    generated_examples: List[str] = Field(
        default_factory=list,
        description="AI-generated examples of similar user scenarios"
    )


class RecipeAssignmentResult(BaseModel):
    """Result of recipe assignment validation"""
    is_appropriate: bool = Field(..., description="Whether recipe fits the scenario")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in assignment")
    reasoning: str = Field(..., description="Explanation of the decision")
    concerns: List[str] = Field(default_factory=list, description="Any concerns or caveats")


class RecipeContext(BaseModel):
    """Complete context for a recipe assignment with evidence and scenarios"""
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    recipe_id: PyObjectId = Field(..., description="MongoDB ObjectId of the recipe")
    
    # Core data
    evidence: List[Evidence] = Field(
        default_factory=list,
        description="Evidence supporting this recipe assignment"
    )
    scenarios: List[UserScenario] = Field(
        default_factory=list,
        description="User scenarios this recipe is validated for"
    )
    
    # Assignment validation
    assignment_result: Optional[RecipeAssignmentResult] = Field(
        None,
        description="Result of AI validation"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    validation_version: str = Field(default="v1", description="Version of validation logic used")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        
    def add_evidence(self, evidence: Evidence) -> None:
        """Add new evidence to the recipe context"""
        self.evidence.append(evidence)
        self.updated_at = datetime.utcnow()
    
    def add_scenario(self, scenario: UserScenario) -> None:
        """Add new user scenario"""
        self.scenarios.append(scenario)
        self.updated_at = datetime.utcnow()
    
    @property
    def validated_evidence_count(self) -> int:
        """Count of validated evidence items"""
        return sum(1 for e in self.evidence if e.validation_status == EvidenceStatus.VALIDATED)
    
    @property
    def is_fully_validated(self) -> bool:
        """Check if all evidence is validated and assignment approved"""
        return (
            all(e.validation_status == EvidenceStatus.VALIDATED for e in self.evidence)
            and self.assignment_result is not None
            and self.assignment_result.is_appropriate
        )