from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db, get_cache_service
from app.schemas import (
    FlagCreate, FlagUpdate, FlagResponse, 
    EvaluationRequest, EvaluationResponse,
    AuditLogResponse
)
from app.services.flag_service import FlagService
from app.services.cache_service import CacheService

router = APIRouter(prefix="/flags", tags=["flags"])


def get_flag_service(cache: CacheService = Depends(get_cache_service)) -> FlagService:
    """Dependency to get FlagService with cache"""
    return FlagService(cache=cache)


@router.post("/", response_model=FlagResponse, status_code=201)
def create_flag(
    flag: FlagCreate,
    db: Session = Depends(get_db),
    flag_service: FlagService = Depends(get_flag_service)
):
    """Create a new feature flag"""
    try:
        new_flag = flag_service.create_flag(db, flag)
        return new_flag
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[FlagResponse])
def list_flags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    flag_service: FlagService = Depends(get_flag_service)
):
    """List all feature flags"""
    flags = flag_service.get_all_flags(db, skip=skip, limit=limit)
    return flags


@router.get("/{flag_key}", response_model=FlagResponse)
def get_flag(
    flag_key: str,
    db: Session = Depends(get_db),
    flag_service: FlagService = Depends(get_flag_service)
):
    """Get a specific feature flag"""
    flag = flag_service.get_flag(db, flag_key)
    if not flag:
        raise HTTPException(status_code=404, detail=f"Flag '{flag_key}' not found")
    return flag


@router.put("/{flag_key}", response_model=FlagResponse)
def update_flag(
    flag_key: str,
    flag_update: FlagUpdate,
    db: Session = Depends(get_db),
    flag_service: FlagService = Depends(get_flag_service)
):
    """Update a feature flag"""
    flag = flag_service.update_flag(db, flag_key, flag_update)
    if not flag:
        raise HTTPException(status_code=404, detail=f"Flag '{flag_key}' not found")
    return flag


@router.delete("/{flag_key}", status_code=204)
def delete_flag(
    flag_key: str,
    db: Session = Depends(get_db),
    flag_service: FlagService = Depends(get_flag_service)
):
    """Delete a feature flag"""
    success = flag_service.delete_flag(db, flag_key)
    if not success:
        raise HTTPException(status_code=404, detail=f"Flag '{flag_key}' not found")
    return None


@router.get("/{flag_key}/evaluate", response_model=EvaluationResponse)
def evaluate_flag(
    flag_key: str,
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    flag_service: FlagService = Depends(get_flag_service)
):
    """Evaluate if a flag is enabled for a user"""
    enabled, reason = flag_service.evaluate_flag(db, flag_key, user_id)
    
    return EvaluationResponse(
        key=flag_key,
        enabled=enabled,
        reason=reason
    )


@router.get("/{flag_key}/audit", response_model=List[AuditLogResponse])
def get_flag_audit_logs(
    flag_key: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    flag_service: FlagService = Depends(get_flag_service)
):
    """Get audit logs for a specific flag"""
    logs = flag_service.get_audit_logs(db, flag_key=flag_key, limit=limit)
    return logs


@router.get("/_cache/stats")
def get_cache_stats(
    cache: CacheService = Depends(get_cache_service)
):
    """Get cache statistics (admin endpoint)"""
    return cache.get_stats()


@router.post("/_cache/clear", status_code=204)
def clear_cache(
    cache: CacheService = Depends(get_cache_service)
):
    """Clear all cached flags (admin endpoint - use with caution!)"""
    cache.clear_all()
    return None
