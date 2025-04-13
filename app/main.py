from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import engine, get_db
from .models import Base
from .routes import api_router
from .utils.auth import get_password_hash


# Create tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Scorecards API", description="API for managing business scorecards")

# CORS configuration - modify as needed for your deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Logiclabs API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Add a convenient endpoint to create the initial admin user
@app.post("/setup/init", include_in_schema=True)
async def initialize_db(
    business_name: str,
    admin_username: str,
    admin_email: str,
    admin_password: str,
    db: Session = Depends(get_db)
):
    from .models import Business, User
    
    # Check if any businesses exist
    business_count = db.query(Business).count()
    if business_count > 0:
        return {"message": "Database already initialized"}
    
    # Create a new business
    new_business = Business(name=business_name)
    db.add(new_business)
    db.flush()
    
    # Create admin user
    hashed_password = get_password_hash(admin_password)
    new_user = User(
        username=admin_username,
        email=admin_email,
        hashed_password=hashed_password,
        business_id=new_business.id,
        is_admin=True
    )
    db.add(new_user)
    db.commit()
    
    return {"message": "Database initialized with business and admin user"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)