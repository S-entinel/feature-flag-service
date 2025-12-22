import hashlib
import json
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.flag import Flag, AuditLog
from app.schemas import FlagCreate, FlagUpdate
from app.services.cache_service import CacheService


class FlagService:
    """Service for managing feature flags with Redis caching"""
    
    def __init__(self, cache: Optional[CacheService] = None):
        """
        Initialize FlagService
        
        Args:
            cache: Optional CacheService instance for caching
        """
        self.cache = cache
    
    def create_flag(self, db: Session, flag_data: FlagCreate, user: Optional[str] = None) -> Flag:
        """Create a new feature flag"""
        # Check if key already exists
        existing = db.query(Flag).filter(Flag.key == flag_data.key).first()
        if existing:
            raise ValueError(f"Flag with key '{flag_data.key}' already exists")
        
        # Create flag
        flag = Flag(**flag_data.model_dump())
        db.add(flag)
        db.commit()
        db.refresh(flag)
        
        # Cache the new flag
        if self.cache:
            flag_dict = self._flag_to_dict(flag)
            self.cache.set_flag(flag.key, flag_dict)
        
        # Create audit log
        audit = AuditLog(
            flag_id=flag.id,
            action="created",
            user=user,
            new_value=json.dumps(flag_data.model_dump())
        )
        db.add(audit)
        db.commit()
        
        return flag
    
    def get_flag(self, db: Session, flag_key: str) -> Optional[Flag]:
        """Get a flag by key (with caching)"""
        # Try cache first
        if self.cache:
            cached = self.cache.get_flag(flag_key)
            if cached:
                # Reconstruct Flag object from cache
                return self._dict_to_flag(cached)
        
        # Cache miss - fetch from database
        flag = db.query(Flag).filter(Flag.key == flag_key).first()
        
        # Store in cache for next time
        if flag and self.cache:
            flag_dict = self._flag_to_dict(flag)
            self.cache.set_flag(flag.key, flag_dict)
        
        return flag
    
    def get_all_flags(self, db: Session, skip: int = 0, limit: int = 100) -> List[Flag]:
        """Get all flags with pagination (not cached - admin operation)"""
        return db.query(Flag).offset(skip).limit(limit).all()
    
    def update_flag(self, db: Session, flag_key: str, flag_data: FlagUpdate, user: Optional[str] = None) -> Optional[Flag]:
        """Update a flag and invalidate cache"""
        flag = db.query(Flag).filter(Flag.key == flag_key).first()
        if not flag:
            return None
        
        # Store old values
        old_values = {
            "name": flag.name,
            "description": flag.description,
            "enabled": flag.enabled,
            "rollout_percentage": flag.rollout_percentage
        }
        
        # Update fields
        update_data = flag_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(flag, field, value)
        
        db.commit()
        db.refresh(flag)
        
        # Invalidate cache since flag changed
        if self.cache:
            self.cache.invalidate_flag(flag.key)
        
        # Create audit log
        audit = AuditLog(
            flag_id=flag.id,
            action="updated",
            user=user,
            old_value=json.dumps(old_values),
            new_value=json.dumps(update_data)
        )
        db.add(audit)
        db.commit()
        
        return flag
    
    def delete_flag(self, db: Session, flag_key: str, user: Optional[str] = None) -> bool:
        """Delete a flag and remove from cache"""
        flag = db.query(Flag).filter(Flag.key == flag_key).first()
        if not flag:
            return False
        
        # Invalidate cache
        if self.cache:
            self.cache.invalidate_flag(flag.key)
        
        # Create audit log before deletion
        audit = AuditLog(
            flag_id=flag.id,
            action="deleted",
            user=user,
            old_value=json.dumps({
                "key": flag.key,
                "name": flag.name,
                "enabled": flag.enabled
            })
        )
        db.add(audit)
        
        db.delete(flag)
        db.commit()
        
        return True
    
    def evaluate_flag(self, db: Session, flag_key: str, user_id: Optional[str] = None) -> tuple[bool, str]:
        """
        Evaluate if a flag is enabled for a user (with caching)
        Returns: (enabled: bool, reason: str)
        """
        # Try cache first for evaluation result
        if self.cache:
            cached_eval = self.cache.get_evaluation(flag_key, user_id)
            if cached_eval:
                return cached_eval
        
        # Cache miss - evaluate from database
        flag = self.get_flag(db, flag_key)  # This uses flag cache
        
        if not flag:
            result = (False, "Flag not found")
            if self.cache:
                self.cache.set_evaluation(flag_key, *result, user_id=user_id)
            return result
        
        if not flag.enabled:
            result = (False, "Flag is disabled")
            if self.cache:
                self.cache.set_evaluation(flag_key, *result, user_id=user_id)
            return result
        
        # If rollout is 100%, enable for everyone
        if flag.rollout_percentage >= 100:
            result = (True, "Flag enabled for all users")
            if self.cache:
                self.cache.set_evaluation(flag_key, *result, user_id=user_id)
            return result
        
        # If rollout is 0%, disable for everyone
        if flag.rollout_percentage <= 0:
            result = (False, "Flag rollout is 0%")
            if self.cache:
                self.cache.set_evaluation(flag_key, *result, user_id=user_id)
            return result
        
        # If no user_id provided, we can't do percentage rollout
        if user_id is None:
            result = (flag.enabled, "Flag enabled (no user targeting)")
            if self.cache:
                self.cache.set_evaluation(flag_key, *result, user_id=user_id)
            return result
        
        # Deterministic percentage rollout using hash
        hash_input = f"{flag.key}:{user_id}"
        hash_value = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)
        bucket = hash_value % 100  # 0-99
        
        enabled = bucket < flag.rollout_percentage
        reason = f"User in {'enabled' if enabled else 'disabled'} rollout bucket ({flag.rollout_percentage}%)"
        
        result = (enabled, reason)
        
        # Cache the evaluation result
        if self.cache:
            self.cache.set_evaluation(flag_key, *result, user_id=user_id)
        
        return result
    
    def get_audit_logs(self, db: Session, flag_key: Optional[str] = None, limit: int = 100) -> List[AuditLog]:
        """Get audit logs, optionally filtered by flag"""
        query = db.query(AuditLog)
        
        if flag_key:
            flag = db.query(Flag).filter(Flag.key == flag_key).first()
            if flag:
                query = query.filter(AuditLog.flag_id == flag.id)
        
        return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def _flag_to_dict(flag: Flag) -> dict:
        """Convert Flag object to dictionary for caching"""
        return {
            "id": flag.id,
            "key": flag.key,
            "name": flag.name,
            "description": flag.description,
            "enabled": flag.enabled,
            "rollout_percentage": flag.rollout_percentage,
            "created_at": flag.created_at.isoformat(),
            "updated_at": flag.updated_at.isoformat()
        }
    
    @staticmethod
    def _dict_to_flag(data: dict) -> Flag:
        """Convert dictionary from cache back to Flag object (for reading only)"""
        from datetime import datetime
        
        flag = Flag()
        flag.id = data["id"]
        flag.key = data["key"]
        flag.name = data["name"]
        flag.description = data["description"]
        flag.enabled = data["enabled"]
        flag.rollout_percentage = data["rollout_percentage"]
        flag.created_at = datetime.fromisoformat(data["created_at"])
        flag.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return flag