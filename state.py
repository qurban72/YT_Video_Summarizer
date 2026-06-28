# src/state.py
from typing import Optional
from pydantic import BaseModel, Field

class GraphState(BaseModel):
    video_url: str = Field(description="The URL of the youtube video")
    video_id: Optional[str] = Field(default=None, description="The ID of the youtube video")
    transcript: Optional[str] = Field(default=None, description="The transcript of the youtube video")
    summary: Optional[str] = Field(default=None, description="The summary notes of the video")
    pdf_path: Optional[str] = Field(default=None, description="Path to the generated PDF file")
    error_message: Optional[str] = Field(default=None, description="Error message if any step fails")