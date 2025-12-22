"""
Data models for the Feature Flag SDK
"""

from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class Flag:
    """Represents a feature flag"""
    id: int
    key: str
    name: str
    description: Optional[str]
    enabled: bool
    rollout_percentage: float
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_dict(cls, data: dict) -> "Flag":
        """Create Flag from API response dictionary"""
        return cls(
            id=data["id"],
            key=data["key"],
            name=data["name"],
            description=data.get("description"),
            enabled=data["enabled"],
            rollout_percentage=data["rollout_percentage"],
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
        )
    
    def to_dict(self) -> dict:
        """Convert Flag to dictionary"""
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "rollout_percentage": self.rollout_percentage,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


@dataclass
class EvaluationResult:
    """Result of a flag evaluation"""
    key: str
    enabled: bool
    reason: str
    
    @classmethod
    def from_dict(cls, data: dict) -> "EvaluationResult":
        """Create EvaluationResult from API response"""
        return cls(
            key=data["key"],
            enabled=data["enabled"],
            reason=data["reason"]
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "key": self.key,
            "enabled": self.enabled,
            "reason": self.reason
        }