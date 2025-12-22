from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Flag(Base):
    """Feature flag model"""
    __tablename__ = "flags"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=False, nullable=False)
    rollout_percentage = Column(Float, default=100.0, nullable=False)  # 0-100
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    audit_logs = relationship("AuditLog", back_populates="flag", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Flag(key={self.key}, enabled={self.enabled})>"


class AuditLog(Base):
    """Audit log for flag changes"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    flag_id = Column(Integer, ForeignKey("flags.id"), nullable=False)
    action = Column(String(50), nullable=False)  # created, updated, deleted, toggled
    user = Column(String(255), nullable=True)  # Optional: who made the change
    old_value = Column(Text, nullable=True)  # JSON string of old state
    new_value = Column(Text, nullable=True)  # JSON string of new state
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    flag = relationship("Flag", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(flag_id={self.flag_id}, action={self.action})>"