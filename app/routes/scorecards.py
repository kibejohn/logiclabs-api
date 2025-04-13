from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional

from ..database import get_db
from ..models import Scorecard, ScorecardVersion, User, Business
from ..schemas import (
    ScorecardCreate,
    Scorecard as ScorecardSchema,
    ScorecardUpdate,
    ScorecardVersion as ScorecardVersionSchema,
)
from ..utils.auth import get_current_active_user

router = APIRouter(
    prefix="/scorecards",
    tags=["scorecards"],
)

@router.post("/", response_model=ScorecardSchema, status_code=status.HTTP_201_CREATED)
def create_scorecard(
    scorecard: ScorecardCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):  
    userBusiness = current_user.business_id
    # Check if business exists
    business = db.query(Business).filter(Business.id == userBusiness).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Check if user belongs to the business
    if current_user.business_id != userBusiness:
        raise HTTPException(status_code=403, detail="Not authorized to create scorecards for this business")
    
    # Create scorecard with percentage_threshold
    db_scorecard = Scorecard(
        **scorecard.dict(),
        created_by_id=current_user.id,
        business_id=userBusiness
    )
    db.add(db_scorecard)
    db.commit()
    db.refresh(db_scorecard)

    # Create initial version with percentage_threshold
    percentage_threshold=scorecard.percentage_threshold if scorecard.percentage_threshold else None
    initial_version = ScorecardVersion(
        scorecard_id=db_scorecard.id,
        version_number=1,
        data=scorecard.data,
        created_by_id=current_user.id,
        comment="Initial version",
        percentage_threshold=percentage_threshold
    )
    db.add(initial_version)
    db.commit()
    
    return db_scorecard


@router.get("/", response_model=List[ScorecardSchema])
def read_scorecards(
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search term to filter scorecards by name, ID, or decision type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Base query to filter by business
    query = db.query(Scorecard).filter(
        Scorecard.business_id == current_user.business_id
    )
    
    # Apply search filter if search term is provided
    if search:
        # Convert search term to lowercase for case-insensitive search
        search_term = f"%{search.lower()}%"
        
        # Search in name, id, and decision_type fields
        query = query.filter(
            or_(
                Scorecard.name.ilike(search_term),
                Scorecard.decision_type.ilike(search_term),
                # For ID search, try to convert search term to integer if possible
                Scorecard.id == search if search.isdigit() else False
            )
        )
    
    # Apply pagination
    scorecards = query.offset(skip).limit(limit).all()
    return scorecards

@router.get("/{scorecard_id}", response_model=ScorecardSchema)
def read_scorecard(
    scorecard_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_scorecard = db.query(Scorecard).filter(Scorecard.id == scorecard_id).first()
    if db_scorecard is None:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    
    # Check if user has access to this scorecard
    if db_scorecard.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this scorecard")
    
    return db_scorecard

@router.get("/{scorecard_id}/versions", response_model=List[ScorecardVersionSchema])
def read_scorecard_versions(
    scorecard_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_scorecard = db.query(Scorecard).filter(Scorecard.id == scorecard_id).first()
    if db_scorecard is None:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    
    # Check if user has access to this scorecard
    if db_scorecard.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this scorecard")
    
    return db_scorecard.versions

@router.get("/{scorecard_id}/version/{version_number}", response_model=ScorecardVersionSchema)
def read_scorecard_version(
    scorecard_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_scorecard = db.query(Scorecard).filter(Scorecard.id == scorecard_id).first()
    if db_scorecard is None:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    
    # Check if user has access to this scorecard
    if db_scorecard.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this scorecard")
    
    version = db.query(ScorecardVersion).filter(
        ScorecardVersion.scorecard_id == scorecard_id,
        ScorecardVersion.version_number == version_number
    ).first()
    
    if version is None:
        raise HTTPException(status_code=404, detail="Version not found")
    
    return version

@router.put("/{scorecard_id}", response_model=ScorecardSchema)
def update_scorecard(
    scorecard_id: int, 
    scorecard: ScorecardUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_scorecard = db.query(Scorecard).filter(Scorecard.id == scorecard_id).first()
    if db_scorecard is None:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    
    # Check if user has access to this scorecard
    if db_scorecard.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this scorecard")
    
    # Get the latest version number
    latest_version = db.query(func.max(ScorecardVersion.version_number)).filter(
        ScorecardVersion.scorecard_id == scorecard_id
    ).scalar() or 0

    # Create a new version if data has changed
    if scorecard.data is not None and scorecard.data != db_scorecard.data:
        new_version = ScorecardVersion(
            scorecard_id=scorecard_id,
            version_number=latest_version + 1,
            data=scorecard.data,
            percentage_threshold = scorecard.percentage_threshold,
            created_by_id=current_user.id,
            comment=f"Version {latest_version + 1}"
        )
        db.add(new_version)
        db_scorecard.version_id = latest_version + 1
    
    # Update scorecard fields
    for key, value in scorecard.dict(exclude_unset=True).items():
        setattr(db_scorecard, key, value)
    
    db.commit()
    db.refresh(db_scorecard)
    return db_scorecard

@router.delete("/{scorecard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scorecard(
    scorecard_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_scorecard = db.query(Scorecard).filter(Scorecard.id == scorecard_id).first()
    if db_scorecard is None:
        raise HTTPException(status_code=404, detail="Scorecard not found")
    
    # Check if user has access to this scorecard
    if db_scorecard.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this scorecard")
    
    # Delete all versions first
    db.query(ScorecardVersion).filter(ScorecardVersion.scorecard_id == scorecard_id).delete()
    
    # Then delete the scorecard
    db.delete(db_scorecard)
    db.commit()
    return None


@router.get("/count", response_model=int)
def count_scorecards(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns the number of scorecards belonging to the current user's business.
    """
    count = db.query(func.count(Scorecard.id)).filter(
        Scorecard.business_id == current_user.business_id
    ).scalar()

    return count
