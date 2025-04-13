from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, Business
from ..schemas import UserCreate, User as UserSchema, UserUpdate, TeamMemberCreate
from ..utils.auth import get_password_hash, get_current_active_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate, 
    db: Session = Depends(get_db)
   # current_user: User = Depends(get_current_active_user)
):
    # Check if the business exists
    business = db.query(Business).filter(Business.id == user.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Check if the user has permission to create users in this business
    # if current_user.business_id != user.business_id and not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Not authorized to create users in this business")
    
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        business_id=user.business_id,
        is_admin=user.is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[UserSchema])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # If admin, can see all users; otherwise, only users in the same business
    if current_user.is_admin:
        users = db.query(User).offset(skip).limit(limit).all()
    else:
        users = db.query(User).filter(
            User.business_id == current_user.business_id
        ).offset(skip).limit(limit).all()
    return users

@router.get("/team", response_model=List[UserSchema])
def get_team_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all team members (users in the same business)
    """
    # Get all users in the same business
    team_members = db.query(User).filter(
        User.business_id == current_user.business_id
    ).all()
    
    return team_members

@router.post("/team", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_team_member(
    team_member: TeamMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new team member in the same business
    """
    # Check if username already exists
    db_user = db.query(User).filter(User.username == team_member.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists
    db_user = db.query(User).filter(User.email == team_member.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user in the same business as the current user
    hashed_password = get_password_hash(team_member.password)
    db_user = User(
        username=team_member.username,
        email=team_member.email,
        hashed_password=hashed_password,
        business_id=current_user.business_id,
        is_admin=False  # Default to non-admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.put("/me", response_model=UserSchema)
def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Only allow updating username for now
    if user_update.username:
        # Check if username is already taken
        existing_user = db.query(User).filter(
            User.username == user_update.username,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        current_user.username = user_update.username
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/{user_id}", response_model=UserSchema)
def read_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if current user has permission to view this user
    if db_user.business_id != current_user.business_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this user")
    
    return db_user

@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if current user has permission to update this user
    if db_user.id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    
    # Update user fields
    for key, value in user_update.dict(exclude_unset=True).items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if current user has permission to delete this user
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete users")
    
    db.delete(db_user)
    db.commit()
    return None
