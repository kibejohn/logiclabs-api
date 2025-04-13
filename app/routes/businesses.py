from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Business, User
from ..schemas import BusinessCreate, Business as BusinessSchema, BusinessUpdate
from ..utils.auth import get_current_active_user

router = APIRouter(
    prefix="/businesses",
    tags=["businesses"],
)

@router.post("/", response_model=BusinessSchema, status_code=status.HTTP_201_CREATED)
def create_business(
    business: BusinessCreate, 
    db: Session = Depends(get_db),
):
    db_business = Business(**business.dict())
    db.add(db_business)
    db.commit()
    db.refresh(db_business)
    return db_business


@router.get("/", response_model=List[BusinessSchema])
def read_businesses(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # In a real app, you might want to filter businesses based on user permissions
    businesses = db.query(Business).offset(skip).limit(limit).all()
    return businesses




@router.get("/current", response_model=BusinessSchema)
def get_current_business(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the current business for the authenticated user.
    
    Returns:
        The business associated with the current user.
        
    Raises:
        HTTPException: If the user doesn't have an associated business.
    """
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No business associated with this user"
        )
    
    db_business = db.query(Business).filter(Business.id == current_user.business_id).first()
    if db_business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found"
        )
    
    return db_business


@router.get("/{business_id}", response_model=BusinessSchema)
def read_business(
    business_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # In a real app, you might want to check if user has access to this business
    db_business = db.query(Business).filter(Business.id == business_id).first()
    if db_business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return db_business


@router.put("/{business_id}", response_model=BusinessSchema)
def update_business(
    business_id: int, 
    business: BusinessUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if business exists
    db_business = db.query(Business).filter(Business.id == business_id).first()
    if db_business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # In a real app, check if current user has permission to update this business
    
    # Update business fields
    for key, value in business.dict(exclude_unset=True).items():
        setattr(db_business, key, value)
    
    db.commit()
    db.refresh(db_business)
    return db_business

@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_business(
    business_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Check if business exists
    db_business = db.query(Business).filter(Business.id == business_id).first()
    if db_business is None:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # In a real app, check if current user has permission to delete this business
    
    db.delete(db_business)
    db.commit()
    return None
