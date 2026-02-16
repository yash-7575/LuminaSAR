"""Pydantic request models for the LuminaSAR API."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.config import SUPPORTED_JURISDICTIONS


class GenerateSARRequest(BaseModel):
    """Request body for SAR generation."""

    case_id: str = Field(..., description="The SAR case ID to generate narrative for")
    force_regenerate: bool = Field(
        default=False, description="Force regenerate even if narrative exists"
    )
    jurisdiction: Optional[str] = Field(
        default=None,
        description="Override jurisdiction for this generation (e.g. IN, US, UK, EU, SG, HK, UAE, AU)",
    )

    @field_validator("jurisdiction")
    @classmethod
    def validate_jurisdiction(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in SUPPORTED_JURISDICTIONS:
            raise ValueError(
                f"Unsupported jurisdiction '{v}'. Must be one of: {', '.join(SUPPORTED_JURISDICTIONS)}"
            )
        return v


class ApproveSARRequest(BaseModel):
    """Request body for SAR approval."""

    analyst_name: str = Field(
        default="Compliance Analyst", description="Name of the approving analyst"
    )
    notes: Optional[str] = Field(default=None, description="Analyst approval notes")
