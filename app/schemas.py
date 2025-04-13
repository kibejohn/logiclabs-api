from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_admin: bool = False

class UserCreate(UserBase):
    password: str
    business_id: int

class TeamMemberCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    business_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class User(UserInDB):
    pass

# Business Schemas
class BusinessBase(BaseModel):
    name: str

class BusinessCreate(BusinessBase):
    pass

class BusinessUpdate(BusinessBase):
    pass

class BusinessInDB(BusinessBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Business(BusinessInDB):
    users: List[User] = []

# Scorecard Schemas
class ScorecardVersionBase(BaseModel):
    version_number: int
    data: Dict[str, Any]
    comment: Optional[str] = None

class ScorecardVersionCreate(ScorecardVersionBase):
    scorecard_id: int
    created_by_id: int

class ScorecardVersion(ScorecardVersionBase):
    id: int
    scorecard_id: int
    created_by_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ScorecardBase(BaseModel):
    name: str
    decision_type: Optional[str] = "scoring"
    version_id: Optional[int] = 0
    decision_model_id: Optional[int] = None
    data: Optional[Dict[str, Any]] = None
    percentage_threshold: Optional[float]  # Add this field
    

class ScorecardCreate(ScorecardBase):
    name: str
    decision_type: str
    data: dict
    percentage_threshold: Optional[float]  # Add this field

    class Config:
        from_attributes = True

class ScorecardUpdate(BaseModel):
    name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    version_id: Optional[int] = None
    decision_model_id: Optional[int] = None
    decision_type: Optional[str] = None
    percentage_threshold: Optional[float]  # Add this field
    

class Scorecard(ScorecardBase):
    id: int
    business_id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    versions: List[ScorecardVersion] = []

    class Config:
        from_attributes = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    
    
class ScoreCalculationRequest(BaseModel):
    input_data: Dict[str, Any]
    nationalId: str
