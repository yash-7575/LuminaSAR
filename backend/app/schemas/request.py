"""Pydantic request models for the LuminaSAR API."""

from pydantic import BaseModel, Field
from typing import Optional


class GenerateSARRequest(BaseModel):
    """Request body for SAR generation."""

    case_id: str = Field(..., description="The SAR case ID to generate narrative for")
    force_regenerate: bool = Field(
        default=False, description="Force regenerate even if narrative exists"
    )


class ApproveSARRequest(BaseModel):
    """Request body for SAR approval."""

    analyst_name: str = Field(
        default="Compliance Analyst", description="Name of the approving analyst"
    )
    notes: Optional[str] = Field(default=None, description="Analyst approval notes")
