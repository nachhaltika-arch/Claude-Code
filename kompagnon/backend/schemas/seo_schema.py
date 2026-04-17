from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class KeywordItem(BaseModel):
    keyword: str
    type: str
    priority: str
    volume: int


class OnpageIssue(BaseModel):
    status: str
    label: str
    description: str


class CompetitorItem(BaseModel):
    name: str
    score: int


class ActionItem(BaseModel):
    title: str
    time: str
    effect: str


class SeoAnalysisBase(BaseModel):
    project_id: int
    trade: Optional[str] = None
    city: Optional[str] = None
    radius_km: Optional[int] = 25


class SeoAnalysisResult(BaseModel):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    trade: Optional[str] = None
    city: Optional[str] = None
    radius_km: Optional[int] = None
    overall_score: Optional[int] = None
    keyword_score: Optional[int] = None
    onpage_score: Optional[int] = None
    competitor_score: Optional[int] = None
    top_keywords: List[Any] = []
    onpage_issues: List[Any] = []
    competitors: List[Any] = []
    action_plan: List[Any] = []
    status: str = "pending"
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
