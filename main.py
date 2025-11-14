from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from typing import Optional
from datetime import timedelta
from pydantic import BaseModel
import logging

from app.database import get_session, create_db_and_tables
from app.models import User, UserCreate, UserRead
from app.auth import (
    create_magic_link,
    verify_magic_link,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.budgets import router as budgets_router
from app.categories import router as categories_router
from app.budget_items import router as budget_items_router
from app.transactions import router as transactions_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Budget Compass API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
     allow_origins=["http://localhost:4200", "http://127.0.0.1:4200",
                    "https://budget-compass.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(budgets_router)
app.include_router(categories_router)
app.include_router(budget_items_router)
app.include_router(transactions_router)

# Request models
class LoginRequest(BaseModel):
    email: str

# Create tables on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
async def root():
    return {"message": "Budget Compass API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Authentication endpoints
@app.post("/api/auth/login")
async def login(request: LoginRequest, session: Session = Depends(get_session)):
    """Request a magic link login."""
    if not request.email or "@" not in request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address"
        )
    
    # Create a magic link and log it (in a real app, send via email)
    token = create_magic_link(request.email, session)
    
    return {"message": "Magic link created. Check the server logs."}

@app.post("/api/auth/verify")
async def verify(request: dict, session: Session = Depends(get_session)):
    """Verify a magic link and return a JWT token."""
    if "token" not in request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
    
    token = request["token"]
    user = verify_magic_link(token, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=UserRead)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get the current user's information."""
    return current_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

