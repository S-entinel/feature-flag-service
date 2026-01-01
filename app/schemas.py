from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class FlagCreate(BaseModel):
    """Schema for creating a new flag"""
    key: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Unique identifier for the flag (lowercase letters, numbers, hyphens, underscores only)"
    )
    name: str = Field(..., min_length=1, max_length=200, description="Human-readable name")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    enabled: bool = Field(default=False, description="Whether the flag is enabled")
    rollout_percentage: float = Field(
        default=100.0, 
        ge=0.0, 
        le=100.0,
        description="Percentage of users to enable (0-100)"
    )
    
    @field_validator('key')
    @classmethod
    def validate_key(cls, v: str) -> str:
        """Validate flag key format and reserved words"""
        # Convert to lowercase
        v = v.lower().strip()
        
        # Check format (alphanumeric, hyphens, underscores only)
        if not re.match(r'^[a-z0-9_-]+$', v):
            raise ValueError(
                "Flag key must contain only lowercase letters, numbers, hyphens, and underscores"
            )
        
        # Check reserved keywords
        reserved_keywords = {
            'health', 'admin', 'api', 'cache', 'stats', 
            'system', 'internal', 'test', 'debug'
        }
        if v in reserved_keywords:
            raise ValueError(
                f"Flag key '{v}' is reserved. Please choose a different key."
            )
        
        # Prevent keys that look like endpoints
        if v.startswith('_'):
            raise ValueError("Flag keys cannot start with underscore")
        
        return v
    
    @field_validator('rollout_percentage')
    @classmethod
    def validate_rollout(cls, v: float) -> float:
        """Ensure rollout percentage is valid"""
        if v < 0 or v > 100:
            raise ValueError("Rollout percentage must be between 0 and 100")
        return round(v, 2)  # Round to 2 decimal places


class FlagUpdate(BaseModel):
    """Schema for updating a flag"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    enabled: Optional[bool] = None
    rollout_percentage: Optional[float] = Field(None, ge=0.0, le=100.0)
    
    @field_validator('rollout_percentage')
    @classmethod
    def validate_rollout(cls, v: Optional[float]) -> Optional[float]:
        """Ensure rollout percentage is valid"""
        if v is not None:
            if v < 0 or v > 100:
                raise ValueError("Rollout percentage must be between 0 and 100")
            return round(v, 2)
        return v


class FlagResponse(BaseModel):
    """Schema for flag response"""
    id: int
    key: str
    name: str
    description: Optional[str]
    enabled: bool
    rollout_percentage: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EvaluationRequest(BaseModel):
    """Schema for flag evaluation request"""
    user_id: Optional[str] = Field(None, max_length=255)


class EvaluationResponse(BaseModel):
    """Schema for flag evaluation response"""
    key: str
    enabled: bool
    reason: str


class AuditLogResponse(BaseModel):
    """Schema for audit log entry"""
    id: int
    flag_id: int
    action: str
    user: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True