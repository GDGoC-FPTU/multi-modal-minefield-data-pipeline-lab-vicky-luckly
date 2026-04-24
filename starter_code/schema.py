from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime

# ==========================================
# ROLE 1: LEAD DATA ARCHITECT
# ==========================================
# Your task is to define the Unified Schema for all sources.
# This is v1. Note: A breaking change is coming at 11:00 AM!

class UnifiedDocument(BaseModel):
    document_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    source_type: str = Field(..., min_length=1) # e.g., 'PDF', 'Video', 'HTML', 'CSV', 'Code'
    author: Optional[str] = "Unknown"
    timestamp: Optional[datetime] = None

    # Source-specific fields live here so the shared contract stays stable.
    source_metadata: Dict[str, Any] = Field(default_factory=dict)
