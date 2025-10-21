from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from app.database import get_session
from app.models import (
    User, Budget, BudgetCreate, BudgetRead, 
    Category, CategoryCreate, CategoryRead,
    BudgetItem, BudgetItemCreate, BudgetItemRead
)
from app.auth import get_current_user

router = APIRouter(prefix="/api/budgets", tags=["budgets"])

# Category endpoints
@router.post("/categories", response_model=CategoryRead)
async def create_category(
    category: CategoryCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new budget category."""
    db_category = Category(
        **category.dict(),
        user_id=current_user.id
    )
    session.add(db_category)
    session.commit()
    session.refresh(db_category)
    return db_category

@router.get("/categories", response_model=List[CategoryRead])
async def get_categories(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all categories for the current user."""
    categories = session.exec(
        select(Category)
        .where(Category.user_id == current_user.id)
        .where(Category.is_active == True)
    ).all()
    return categories

@router.get("/categories/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific category by ID."""
    category = session.exec(
        select(Category)
        .where(Category.id == category_id)
        .where(Category.user_id == current_user.id)
        .where(Category.is_active == True)
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category

# Budget endpoints
@router.post("", response_model=BudgetRead)
async def create_budget(
    budget: BudgetCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new monthly budget."""
    # Check if a budget already exists for this month/year
    existing_budget = session.exec(
        select(Budget)
        .where(Budget.user_id == current_user.id)
        .where(Budget.month == budget.month)
        .where(Budget.year == budget.year)
        .where(Budget.is_active == True)
    ).first()
    
    if existing_budget:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A budget for {budget.month}/{budget.year} already exists"
        )
    
    # Auto-generate the name
    month_name = datetime(budget.year, budget.month, 1).strftime('%B')
    budget_name = f"{month_name} {budget.year}"

    db_budget = Budget(
        month=budget.month,
        year=budget.year,
        name=budget_name,
        user_id=current_user.id
    )
    session.add(db_budget)
    session.commit()
    session.refresh(db_budget)
    return db_budget

@router.get("", response_model=List[BudgetRead])
async def get_budgets(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all budgets for the current user."""
    budgets = session.exec(
        select(Budget)
        .where(Budget.user_id == current_user.id)
        .where(Budget.is_active == True)
        .order_by(Budget.year.desc(), Budget.month.desc())
    ).all()
    return budgets

@router.get("/current", response_model=BudgetRead)
async def get_current_budget(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get the current month's budget or the most recent one."""
    now = datetime.now()
    current_month = now.month
    current_year = now.year
    
    # Try to find the current month's budget
    budget = session.exec(
        select(Budget)
        .where(Budget.user_id == current_user.id)
        .where(Budget.month == current_month)
        .where(Budget.year == current_year)
        .where(Budget.is_active == True)
    ).first()
    
    # If not found, get the most recent budget
    if not budget:
        budget = session.exec(
            select(Budget)
            .where(Budget.user_id == current_user.id)
            .where(Budget.is_active == True)
            .order_by(Budget.year.desc(), Budget.month.desc())
        ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No budgets found"
        )
    
    return budget

@router.get("/{budget_id}", response_model=BudgetRead)
async def get_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific budget by ID."""
    budget = session.exec(
        select(Budget)
        .where(Budget.id == budget_id)
        .where(Budget.user_id == current_user.id)
        .where(Budget.is_active == True)
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    return budget

# Budget Item endpoints
@router.post("/items", response_model=BudgetItemRead)
async def create_budget_item(
    item: BudgetItemCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Add a budget item (category allocation) to a budget."""
    # Verify the budget belongs to the user
    budget = session.exec(
        select(Budget)
        .where(Budget.id == item.budget_id)
        .where(Budget.user_id == current_user.id)
        .where(Budget.is_active == True)
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Verify the category belongs to the user
    category = session.exec(
        select(Category)
        .where(Category.id == item.category_id)
        .where(Category.user_id == current_user.id)
        .where(Category.is_active == True)
    ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if this category is already in the budget
    existing_item = session.exec(
        select(BudgetItem)
        .where(BudgetItem.budget_id == item.budget_id)
        .where(BudgetItem.category_id == item.category_id)
        .where(BudgetItem.is_active == True)
    ).first()
    
    if existing_item:
        # Update the existing item instead of creating a new one
        existing_item.amount = item.amount
        existing_item.updated_at = datetime.utcnow()
        session.add(existing_item)
        session.commit()
        session.refresh(existing_item)
        return existing_item
    
    # Create a new budget item
    db_item = BudgetItem(**item.dict())
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

@router.get("/items/{budget_id}", response_model=List[BudgetItemRead])
async def get_budget_items(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all budget items for a specific budget."""
    # Verify the budget belongs to the user
    budget = session.exec(
        select(Budget)
        .where(Budget.id == budget_id)
        .where(Budget.user_id == current_user.id)
        .where(Budget.is_active == True)
    ).first()
    
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Get all budget items
    items = session.exec(
        select(BudgetItem)
        .where(BudgetItem.budget_id == budget_id)
        .where(BudgetItem.is_active == True)
    ).all()
    
    return items