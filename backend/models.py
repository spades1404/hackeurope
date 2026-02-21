from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

class UserModel(BaseModel):
    id: Optional[str] = None
    email: str
    name: str
    role: str # "worker" or "business"

class CompanyProfile(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    name: str
    jurisdictions: List[str]  # e.g., ["US", "UK", "DE", "AU"]
    entity_types: Dict[str, str]  # e.g., {"US": "c_corp", "UK": "ltd"}
    annual_revenue: float
    employee_count: int
    fiscal_year_ends: Dict[str, str]  # e.g., {"US": "12-31"}

class ActionModel(BaseModel):
    id: str
    company_id: str
    obligation_id: str
    obligation_name: str
    jurisdiction: str
    deadline: str
    prep_start_date: str
    status: str  # upcoming | in_progress | pending_review | approved | submitted | overdue
    priority: str  # overdue | critical | high | medium | low
    document_id: Optional[str] = None
    action_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: str

class DocumentPayload(BaseModel):
    id: str
    action_id: str
    company_id: str
    document_type: str
    content: Dict[str, Any]  # The structured sections of the document
    status: str # draft | pending_approval | approved | submitted
    version: int
    approved_at: Optional[str] = None
    submitted_at: Optional[str] = None
    created_at: str

class ChatMessage(BaseModel):
    role: str # user or model
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
