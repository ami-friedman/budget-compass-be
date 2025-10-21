from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from app.database import get_session
from app.models import User
from app.default_data import create_default_categories
import secrets
import logging

# Configuration
SECRET_KEY = "your-secret-key-here"  # In production, use a secure environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
MAGIC_LINK_EXPIRE_MINUTES = 15

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Store for magic links (in a real app, use Redis or another persistent store)
# Format: {token: email}
magic_links = {}

def create_magic_link(email: str, session: Session) -> str:
    """
    Create a magic link token for the given email.
    If the user does not exist, a new user will be created.
    """
    # Check if user exists
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        # Create a new user if they don't exist
        user = User(email=email)
        session.add(user)
        session.commit()
        session.refresh(user)
        # Create default categories for the new user
        create_default_categories(session, user.id)

    # Generate a secure random token
    token = secrets.token_urlsafe(32)
    
    # Store the token with the email
    magic_links[token] = email
    
    # In a real app, you would send this link via email
    # For now, we'll just log it to the console
    link = f"http://localhost:4200/verify?token={token}"
    logging.info(f"Magic link for {email}: {link}")
    
    return token

def verify_magic_link(token: str, session: Session) -> Optional[User]:
    """Verify a magic link token and return the associated user."""
    if token not in magic_links:
        return None
    
    email = magic_links.pop(token)  # Use the token only once
    
    # Find the user
    user = session.exec(select(User).where(User.email == email)).first()
    
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
) -> User:
    """Get the current user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise credentials_exception
    
    return user