from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class FlagBase(BaseModel):
    """Base flag schema"""
    key: str = Field(..., min_length=1, max_length=255, description="Unique flag key")
    name: str = Field(..., min_length=1, max_length=255, description="Human-readable name")
    description: Optional[str] = Field(None, description="Flag description")
    enabled: bool = Field(default=False, description="Is flag enabled")
    rollout_percentage: float = Field(default=100.0, ge=0.0, le=100.0, description="Rollout percentage (0-100)")
    
    @field_validator('rollout_percentage')
    def validate_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Rollout percentage must be between 0 and 100')
        return v


class FlagCreate(FlagBase):
    """Schema for creating a flag"""
    pass


class FlagUpdate(BaseModel):
    """Schema for updating a flag"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    enabled: Optional[bool] = None
    rollout_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    
    @field_validator('rollout_percentage')
    def validate_percentage(cls, v):
        if v is not None and not 0 <= v <= 100:
            raise ValueError('Rollout percentage must be between 0 and 100')
        return v


class FlagResponse(FlagBase):
    """Schema for flag response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}



class EvaluationRequest(BaseModel):
    """Schema for flag evaluation request"""
    user_id: Optional[str] = Field(None, description="User ID for percentage rollout")


class EvaluationResponse(BaseModel):
    """Schema for flag evaluation response"""
    key: str
    enabled: bool
    reason: str  # Why was this enabled/disabled


class AuditLogResponse(BaseModel):
    """Schema for audit log response"""
    id: int
    flag_id: int
    action: str
    user: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    timestamp: datetime
    
    model_config = {"from_attributes": True}
