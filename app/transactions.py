from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from .database import get_session
from .auth import get_current_user
from .models import (
    Transaction, TransactionCreate, TransactionRead, TransactionUpdate,
    BudgetItem, CategoryType, AccountType, User
)

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.post("/", response_model=TransactionRead)
def create_transaction(
    transaction_data: TransactionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new transaction"""
    
    # Verify the budget item exists and belongs to the user
    budget_item = session.get(BudgetItem, transaction_data.budget_item_id)
    if not budget_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget item not found"
        )
    
    # Check if budget item belongs to user's budget
    if budget_item.budget.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Budget item does not belong to current user"
        )
    
    # Create transaction with user-specified account type
    transaction = Transaction(
        amount=transaction_data.amount,
        description=transaction_data.description,
        transaction_date=transaction_data.transaction_date or datetime.utcnow(),
        account_type=transaction_data.account_type,
        budget_item_id=transaction_data.budget_item_id,
        user_id=current_user.id
    )
    
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    
    return transaction

@router.get("/", response_model=List[TransactionRead])
def get_transactions(
    budget_id: int = None,
    account_type: AccountType = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get transactions for the current user, optionally filtered by budget or account type"""
    
    query = select(Transaction).where(
        Transaction.user_id == current_user.id,
        Transaction.is_active == True
    )
    
    if budget_id:
        # Filter by budget through budget_item relationship
        query = query.join(BudgetItem).where(BudgetItem.budget_id == budget_id)
    
    if account_type:
        query = query.where(Transaction.account_type == account_type)
    
    query = query.order_by(Transaction.transaction_date.desc())
    
    transactions = session.exec(query).all()
    return transactions

@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get a specific transaction"""
    
    transaction = session.get(Transaction, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    if transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Transaction does not belong to current user"
        )
    
    return transaction

@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a transaction"""
    
    transaction = session.get(Transaction, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    if transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Transaction does not belong to current user"
        )
    
    # Update fields if provided
    update_data = transaction_data.model_dump(exclude_unset=True)
    
    # If budget_item_id is being updated, verify it belongs to user
    if "budget_item_id" in update_data:
        budget_item = session.get(BudgetItem, update_data["budget_item_id"])
        if not budget_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Budget item not found"
            )
        
        if budget_item.budget.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Budget item does not belong to current user"
            )
    
    for field, value in update_data.items():
        setattr(transaction, field, value)
    
    transaction.updated_at = datetime.utcnow()
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    
    return transaction

@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a transaction"""
    
    transaction = session.get(Transaction, transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    if transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Transaction does not belong to current user"
        )
    
    # Soft delete
    transaction.is_active = False
    transaction.deleted_at = datetime.utcnow()
    transaction.updated_at = datetime.utcnow()
    
    session.add(transaction)
    session.commit()
    
    return {"message": "Transaction deleted successfully"}

@router.get("/budget/{budget_id}/summary")
def get_budget_transaction_summary(
    budget_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get transaction summary for a specific budget, grouped by category and account type"""
    
    # Verify budget belongs to user
    from .models import Budget
    budget = session.get(Budget, budget_id)
    if not budget or budget.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found"
        )
    
    # Get all transactions for this budget
    query = select(Transaction).join(BudgetItem).where(
        BudgetItem.budget_id == budget_id,
        Transaction.user_id == current_user.id,
        Transaction.is_active == True
    )
    
    transactions = session.exec(query).all()
    
    # Group by account type and calculate totals
    summary = {
        "checking": {
            "total_spent": 0,
            "categories": {}
        },
        "savings": {
            "total_spent": 0,
            "categories": {}
        }
    }
    
    for transaction in transactions:
        account_key = transaction.account_type.value
        category_name = transaction.budget_item.category.name
        
        # Add to total
        summary[account_key]["total_spent"] += float(transaction.amount)
        
        # Add to category breakdown
        if category_name not in summary[account_key]["categories"]:
            summary[account_key]["categories"][category_name] = {
                "budgeted": float(transaction.budget_item.amount),
                "spent": 0,
                "remaining": 0
            }
        
        summary[account_key]["categories"][category_name]["spent"] += float(transaction.amount)
    
    # Calculate remaining amounts
    for account_type in summary:
        for category in summary[account_type]["categories"]:
            cat_data = summary[account_type]["categories"][category]
            cat_data["remaining"] = cat_data["budgeted"] - cat_data["spent"]
    
    return summary