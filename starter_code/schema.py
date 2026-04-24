from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==========================================
# ROLE 1: LEAD DATA ARCHITECT
# ==========================================
# Your task is to define the Unified Schema for all sources.
# This is v1. Note: A breaking change is coming at 11:00 AM!

class UnifiedDocument(BaseModel):
    # TODO: Define the v1 schema. 
    # Suggested fields: document_id, content, source_type, author, timestamp, metadata

    document_id: str = Field(..., min_length=3)
    content: str = Field(..., min_length=1)
    source_type: str = Field(..., min_length=3)  # e.g., 'PDF', 'Video', 'HTML', 'CSV', 'Code'
    author: Optional[str] = "Unknown"
    timestamp: Optional[datetime] = None

    # You might want a dict for source-specific metadata
    source_metadata: dict = Field(default_factory=dict)
