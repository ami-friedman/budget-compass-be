from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from app.database import get_session
from app.models import BudgetItem, BudgetItemCreate, BudgetItemRead, Budget, User
from app.auth import get_current_user

router = APIRouter(
    prefix="/api/budgets/{budget_id}/items",
    tags=["budget-items"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=BudgetItemRead)
def create_budget_item(
    *,
    session: Session = Depends(get_session),
    budget_id: int,
    budget_item: BudgetItemCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Add a new item to a budget.
    """
    # First, verify the budget belongs to the current user
    budget = session.get(Budget, budget_id)
    if not budget or budget.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Budget not found")

    # Check if this category is already in the budget with the same category type
    existing_item = session.exec(
        select(BudgetItem)
        .where(BudgetItem.budget_id == budget_id)
        .where(BudgetItem.category_id == budget_item.category_id)
        .where(BudgetItem.category_type == budget_item.category_type)
        .where(BudgetItem.is_active == True)
    ).first()
    
    if existing_item:
        # Update the existing item instead of creating a new one
        existing_item.amount = budget_item.amount
        session.add(existing_item)
        session.commit()
        session.refresh(existing_item)
        return existing_item
    
    db_budget_item = BudgetItem.model_validate(budget_item, update={"budget_id": budget_id})
    session.add(db_budget_item)
    session.commit()
    session.refresh(db_budget_item)
    return db_budget_item

@router.get("/", response_model=List[BudgetItemRead])
def read_budget_items(
    *,
    session: Session = Depends(get_session),
    budget_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get all items for a specific budget.
    """
    budget = session.get(Budget, budget_id)
    if not budget or budget.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Budget not found")

    return budget.budget_items

@router.patch("/{item_id}", response_model=BudgetItemRead)
def update_budget_item(
    *,
    session: Session = Depends(get_session),
    budget_id: int,
    item_id: int,
    item_update: BudgetItemCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Update a budget item (e.g., change the amount).
    """
    budget = session.get(Budget, budget_id)
    if not budget or budget.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Budget not found")

    db_item = session.get(BudgetItem, item_id)
    if not db_item or db_item.budget_id != budget_id:
        raise HTTPException(status_code=404, detail="Budget item not found")

    item_data = item_update.model_dump(exclude_unset=True)
    for key, value in item_data.items():
        setattr(db_item, key, value)
        
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

@router.delete("/{item_id}")
def delete_budget_item(
    *,
    session: Session = Depends(get_session),
    budget_id: int,
    item_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a budget item.
    """
    budget = session.get(Budget, budget_id)
    if not budget or budget.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Budget not found")

    item = session.get(BudgetItem, item_id)
    if not item or item.budget_id != budget_id:
        raise HTTPException(status_code=404, detail="Budget item not found")
        
    session.delete(item)
    session.commit()
    return {"ok": True}