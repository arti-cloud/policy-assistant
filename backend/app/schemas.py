from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AskRequest(BaseModel):
    question: str
    filters: Optional[Dict[str, str]] = Field(default_factory=dict)
    top_k: Optional[int] = 5
    follow_up_context: Optional[str] = None

class Citation(BaseModel):
    doc_id: str
    section: str
    snippet: str
    page: Optional[int] = None

class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    policy_matches: List[str]
    confidence: str
    disclaimer: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IngestResponse(BaseModel):
    upserted: int
    errors: Optional[List[str]] = None

class Feedback(BaseModel):
    answer_id: str
    helpful: bool
    comment: Optional[str] = None
