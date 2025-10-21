from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models import Category, CategoryCreate, CategoryRead, User
from app.auth import get_current_user

router = APIRouter(
    prefix="/api/categories",
    tags=["categories"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=CategoryRead)
def create_category(
    *,
    session: Session = Depends(get_session),
    category: CategoryCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new category for the current user.
    """
    db_category = Category.model_validate(category, update={"user_id": current_user.id})
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

@router.get("/", response_model=List[CategoryRead])
def read_categories(
    *,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get all active categories for the current user.
    """
    categories = session.exec(
        select(Category).where(Category.user_id == current_user.id, Category.is_active == True)
    ).all()
    return categories

@router.get("/{category_id}", response_model=CategoryRead)
def read_category(
    *,
    session: Session = Depends(get_session),
    category_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific category by ID.
    """
    category = session.get(Category, category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    *,
    session: Session = Depends(get_session),
    category_id: int,
    category_update: CategoryCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Update a category's name.
    """
    db_category = session.get(Category, category_id)
    if not db_category or db_category.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category_data = category_update.model_dump(exclude_unset=True)
    for key, value in category_data.items():
        setattr(db_category, key, value)
        
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

@router.delete("/{category_id}")
def archive_category(
    *,
    session: Session = Depends(get_session),
    category_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Archive a category (soft delete).
    """
    category = session.get(Category, category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category.is_active = False
    session.add(category)
    session.commit()
    return {"ok": True}