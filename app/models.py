from sqlalchemy import Column, Float, Integer, String, Boolean, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class Business(Base):
    __tablename__ = "businesses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="business")
    scorecards = relationship("Scorecard", back_populates="business")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    business = relationship("Business", back_populates="users")
    scorecards = relationship("Scorecard", back_populates="created_by")

class ScorecardVersion(Base):
    __tablename__ = "scorecard_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    scorecard_id = Column(Integer, ForeignKey("scorecards.id"))
    version_number = Column(Integer, nullable=False)
    percentage_threshold = Column(Float, nullable=True)  # Added new field
    data = Column(JSON, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    comment = Column(String(500))
    
    # Relationships
    scorecard = relationship("Scorecard", back_populates="versions")
    created_by = relationship("User")

class Scorecard(Base):
    __tablename__ = "scorecards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    decision_model_id = Column(Integer, nullable=True)
    version_id = Column(Integer, default=0)
    decision_type = Column(String(50), default="scoring")
    percentage_threshold = Column(Float, nullable=True)  # Added new field
    data = Column(JSON, nullable=False)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    business = relationship("Business", back_populates="scorecards")
    created_by = relationship("User", back_populates="scorecards")
    versions = relationship("ScorecardVersion", back_populates="scorecard", order_by="ScorecardVersion.version_number")
    calculations = relationship("ScoreCalculation", back_populates="scorecard")

class ScoreCalculation(Base):
    __tablename__ = "score_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, nullable=False)  # ID of the client for whom the score is calculated
    scorecard_id = Column(Integer, ForeignKey("scorecards.id"))
    version_id = Column(Integer, nullable=True)  # ID of the version used for calculation
    percentage_threshold = Column(Float, nullable=True)  # Added new field
    input_data = Column(JSON, nullable=False)
    score_result = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    decision = Column(String(50), default="Not Applicable")
    missing_attributes = Column(JSON, nullable=True)
    extra_attributes = Column(JSON, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    scorecard = relationship("Scorecard", back_populates="calculations")
    created_by = relationship("User")