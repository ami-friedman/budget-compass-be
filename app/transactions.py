from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from .database import get_session
from .auth import get_current_user
from .models import (
    Transaction, TransactionCreate, TransactionRead, TransactionUpdate,
    BudgetItem, Category, CategoryType, AccountType, User,
    SavingsCategoryBalance
)
from decimal import Decimal

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

@router.post("/", response_model=TransactionRead)
def create_transaction(
    transaction_data: TransactionCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a new transaction"""
    
    # Validate based on account type
    if transaction_data.account_type == AccountType.CHECKING:
        # Checking transactions must have budget_item_id
        if not transaction_data.budget_item_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Checking account transactions must specify a budget_item_id"
            )
        
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
        
        # Create checking transaction
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
        
        # If this is a savings budget item, update the savings balance
        if budget_item.category_type == CategoryType.SAVINGS:
            _update_savings_balance_for_funding(
                session,
                current_user.id,
                budget_item.category_id,
                transaction.amount,
                transaction.id
            )
        
    elif transaction_data.account_type == AccountType.SAVINGS:
        # Savings transactions must have category_id
        if not transaction_data.category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Savings account transactions must specify a category_id"
            )
        
        # Verify the category exists and belongs to the user
        category = session.get(Category, transaction_data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        # Check if category belongs to user
        if category.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Category does not belong to current user"
            )
        
        # Create savings transaction
        transaction = Transaction(
            amount=transaction_data.amount,
            description=transaction_data.description,
            transaction_date=transaction_data.transaction_date or datetime.utcnow(),
            account_type=transaction_data.account_type,
            category_id=transaction_data.category_id,
            user_id=current_user.id
        )
        
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        
        # Update the savings balance for spending
        _update_savings_balance_for_spending(
            session,
            current_user.id,
            transaction_data.category_id,
            transaction.amount,
            transaction.id
        )
    
    return transaction

@router.get("/", response_model=List[TransactionRead])
def get_transactions(
    budget_id: int = None,
    account_type: AccountType = None,
    month: int = None,
    year: int = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get transactions for the current user, optionally filtered by budget, account type, or month/year"""
    
    query = select(Transaction).where(
        Transaction.user_id == current_user.id,
        Transaction.is_active == True
    )
    
    # When filtering by budget_id with month/year, we need to handle both checking and savings
    if budget_id and month is not None and year is not None:
        # For checking transactions: filter through budget_item relationship
        # For savings transactions: just filter by month/year (they don't have budget_item_id)
        from sqlalchemy import extract, or_
        
        checking_filter = (
            Transaction.account_type == AccountType.CHECKING
        ).self_group()
        
        savings_filter = (
            Transaction.account_type == AccountType.SAVINGS
        ).self_group()
        
        # Apply month/year filter to all transactions
        query = query.where(
            extract('month', Transaction.transaction_date) == month,
            extract('year', Transaction.transaction_date) == year
        )
        
        # For checking transactions, also filter by budget
        query = query.outerjoin(BudgetItem).where(
            or_(
                checking_filter & (BudgetItem.budget_id == budget_id),
                savings_filter
            )
        )
    elif budget_id:
        # Filter by budget through budget_item relationship (checking only)
        query = query.join(BudgetItem).where(BudgetItem.budget_id == budget_id)
    elif month is not None and year is not None:
        # Filter by month and year only
        from sqlalchemy import extract
        query = query.where(
            extract('month', Transaction.transaction_date) == month,
            extract('year', Transaction.transaction_date) == year
        )
    
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
    
    # Store old values for balance adjustment
    old_amount = transaction.amount
    old_account_type = transaction.account_type
    old_category_id = transaction.category_id
    old_budget_item_id = transaction.budget_item_id
    
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
    
    # Handle balance updates if amount or category changed
    if old_account_type == AccountType.CHECKING and old_budget_item_id:
        old_budget_item = session.get(BudgetItem, old_budget_item_id)
        if old_budget_item and old_budget_item.category_type == CategoryType.SAVINGS:
            # Reverse old funding
            _update_savings_balance_for_funding(
                session, current_user.id, old_budget_item.category_id, -old_amount, transaction.id
            )
            # Apply new funding if still a savings item
            if transaction.budget_item_id:
                new_budget_item = session.get(BudgetItem, transaction.budget_item_id)
                if new_budget_item and new_budget_item.category_type == CategoryType.SAVINGS:
                    _update_savings_balance_for_funding(
                        session, current_user.id, new_budget_item.category_id, transaction.amount, transaction.id
                    )
    
    elif old_account_type == AccountType.SAVINGS and old_category_id:
        # Reverse old spending
        _update_savings_balance_for_spending(
            session, current_user.id, old_category_id, -old_amount, transaction.id
        )
        # Apply new spending
        if transaction.category_id:
            _update_savings_balance_for_spending(
                session, current_user.id, transaction.category_id, transaction.amount, transaction.id
            )
    
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
    
    # Reverse balance updates before soft delete
    if transaction.account_type == AccountType.CHECKING and transaction.budget_item_id:
        budget_item = session.get(BudgetItem, transaction.budget_item_id)
        if budget_item and budget_item.category_type == CategoryType.SAVINGS:
            # Reverse the funding
            _update_savings_balance_for_funding(
                session, current_user.id, budget_item.category_id, -transaction.amount, transaction.id
            )
    
    elif transaction.account_type == AccountType.SAVINGS and transaction.category_id:
        # Reverse the spending
        _update_savings_balance_for_spending(
            session, current_user.id, transaction.category_id, -transaction.amount, transaction.id
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

def _update_savings_balance_for_funding(
    session: Session,
    user_id: int,
    category_id: int,
    amount: Decimal,
    transaction_id: int
):
    """Update savings balance when a checking transaction funds a savings category"""
    # Get or create balance record
    balance = session.exec(
        select(SavingsCategoryBalance).where(
            SavingsCategoryBalance.user_id == user_id,
            SavingsCategoryBalance.category_id == category_id
        )
    ).first()
    
    if not balance:
        balance = SavingsCategoryBalance(
            user_id=user_id,
            category_id=category_id,
            funded_amount=Decimal("0.00"),
            spent_amount=Decimal("0.00"),
            available_balance=Decimal("0.00")
        )
        session.add(balance)
    
    # Update funded amount and available balance
    balance.funded_amount += amount
    balance.available_balance = balance.funded_amount - balance.spent_amount
    balance.last_transaction_id = transaction_id
    balance.updated_at = datetime.utcnow()
    
    session.commit()

def _update_savings_balance_for_spending(
    session: Session,
    user_id: int,
    category_id: int,
    amount: Decimal,
    transaction_id: int
):
    """Update savings balance when a savings transaction spends from a category"""
    # Get balance record (should exist if category was funded)
    balance = session.exec(
        select(SavingsCategoryBalance).where(
            SavingsCategoryBalance.user_id == user_id,
            SavingsCategoryBalance.category_id == category_id
        )
    ).first()
    
    if not balance:
        # Create balance record even if not previously funded (allows negative balance)
        balance = SavingsCategoryBalance(
            user_id=user_id,
            category_id=category_id,
            funded_amount=Decimal("0.00"),
            spent_amount=Decimal("0.00"),
            available_balance=Decimal("0.00")
        )
        session.add(balance)
    
    # Update spent amount and available balance
    balance.spent_amount += amount
    balance.available_balance = balance.funded_amount - balance.spent_amount
    balance.last_transaction_id = transaction_id
    balance.updated_at = datetime.utcnow()
    
    session.commit()

@router.get("/savings/balances", response_model=List[dict])
def get_savings_balances(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get all savings category balances for the current user"""
    
    balances = session.exec(
        select(SavingsCategoryBalance).where(
            SavingsCategoryBalance.user_id == current_user.id
        )
    ).all()
    
    # Enrich with category names
    result = []
    for balance in balances:
        category = session.get(Category, balance.category_id)
        if category:
            result.append({
                "id": balance.id,
                "category_id": balance.category_id,
                "category_name": category.name,
                "funded_amount": float(balance.funded_amount),
                "spent_amount": float(balance.spent_amount),
                "available_balance": float(balance.available_balance),
                "updated_at": balance.updated_at
            })
    
    return result

@router.get("/savings/balances/{category_id}")
def get_category_balance(
    category_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get savings balance for a specific category"""
    
    # Verify category belongs to user
    category = session.get(Category, category_id)
    if not category or category.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    balance = session.exec(
        select(SavingsCategoryBalance).where(
            SavingsCategoryBalance.user_id == current_user.id,
            SavingsCategoryBalance.category_id == category_id
        )
    ).first()
    
    if not balance:
        # Return zero balance if not funded yet
        return {
            "category_id": category_id,
            "category_name": category.name,
            "funded_amount": 0.0,
            "spent_amount": 0.0,
            "available_balance": 0.0
        }
    
    return {
        "id": balance.id,
        "category_id": balance.category_id,
        "category_name": category.name,
        "funded_amount": float(balance.funded_amount),
        "spent_amount": float(balance.spent_amount),
        "available_balance": float(balance.available_balance),
        "updated_at": balance.updated_at
    }