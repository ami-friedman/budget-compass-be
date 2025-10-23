from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.database import get_session
from app.models import (
    User, Budget, BudgetCreate, BudgetRead,
    Category, CategoryCreate, CategoryRead,
    BudgetItem, BudgetItemCreate, BudgetItemRead,
    Transaction, CategoryType,
    MonthsEndSummary, CategorySummary, ExpensesSummary,
    ExpenseBreakdown, NetPosition
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

@router.get("/months-end-summary", response_model=MonthsEndSummary)
async def get_months_end_summary(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2000, le=2100, description="Year"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get a comprehensive month's end summary showing income vs expenses breakdown.
    
    Returns budgeted vs actual amounts for:
    - Income
    - Expenses (Cash, Monthly, Savings)
    - Net position
    """
    
    # Find budget for the specified month/year
    budget = session.exec(
        select(Budget)
        .where(Budget.user_id == current_user.id)
        .where(Budget.month == month)
        .where(Budget.year == year)
        .where(Budget.is_active == True)
    ).first()
    
    # If no budget exists, return empty summary
    if not budget:
        return MonthsEndSummary(
            budget_id=None,
            month=month,
            year=year,
            budget_name=None,
            has_budget=False,
            income=CategorySummary(budgeted=0.0, actual=0.0, variance=0.0, variance_percentage=0.0),
            expenses=ExpensesSummary(
                total_budgeted=0.0,
                total_actual=0.0,
                total_variance=0.0,
                breakdown=ExpenseBreakdown(
                    cash=CategorySummary(budgeted=0.0, actual=0.0, variance=0.0, variance_percentage=0.0),
                    monthly=CategorySummary(budgeted=0.0, actual=0.0, variance=0.0, variance_percentage=0.0),
                    savings=CategorySummary(budgeted=0.0, actual=0.0, variance=0.0, variance_percentage=0.0)
                )
            ),
            net_position=NetPosition(budgeted=0.0, actual=0.0, variance=0.0)
        )
    
    # Get all budget items for this budget
    budget_items = session.exec(
        select(BudgetItem)
        .where(BudgetItem.budget_id == budget.id)
        .where(BudgetItem.is_active == True)
    ).all()
    
    # Initialize category summaries
    category_data = {
        CategoryType.INCOME: {"budgeted": 0.0, "actual": 0.0},
        CategoryType.CASH: {"budgeted": 0.0, "actual": 0.0},
        CategoryType.MONTHLY: {"budgeted": 0.0, "actual": 0.0},
        CategoryType.SAVINGS: {"budgeted": 0.0, "actual": 0.0}
    }
    
    # Sum budgeted amounts by category type
    for item in budget_items:
        category_data[item.category_type]["budgeted"] += item.amount
    
    # Get actual spending from transactions
    for item in budget_items:
        # Get all transactions for this budget item
        transactions = session.exec(
            select(Transaction)
            .where(Transaction.budget_item_id == item.id)
            .where(Transaction.is_active == True)
        ).all()
        
        # Sum transaction amounts
        total_spent = sum(float(t.amount) for t in transactions)
        category_data[item.category_type]["actual"] += total_spent
    
    # Helper function to calculate variance
    def calculate_variance(budgeted: float, actual: float) -> tuple[float, float]:
        """Calculate variance and variance percentage"""
        variance = actual - budgeted
        variance_pct = (variance / budgeted * 100) if budgeted != 0 else 0.0
        return variance, variance_pct
    
    # Create category summaries
    income_variance, income_variance_pct = calculate_variance(
        category_data[CategoryType.INCOME]["budgeted"],
        category_data[CategoryType.INCOME]["actual"]
    )
    
    cash_variance, cash_variance_pct = calculate_variance(
        category_data[CategoryType.CASH]["budgeted"],
        category_data[CategoryType.CASH]["actual"]
    )
    
    monthly_variance, monthly_variance_pct = calculate_variance(
        category_data[CategoryType.MONTHLY]["budgeted"],
        category_data[CategoryType.MONTHLY]["actual"]
    )
    
    savings_variance, savings_variance_pct = calculate_variance(
        category_data[CategoryType.SAVINGS]["budgeted"],
        category_data[CategoryType.SAVINGS]["actual"]
    )
    
    # Calculate totals
    total_expenses_budgeted = (
        category_data[CategoryType.CASH]["budgeted"] +
        category_data[CategoryType.MONTHLY]["budgeted"] +
        category_data[CategoryType.SAVINGS]["budgeted"]
    )
    
    total_expenses_actual = (
        category_data[CategoryType.CASH]["actual"] +
        category_data[CategoryType.MONTHLY]["actual"] +
        category_data[CategoryType.SAVINGS]["actual"]
    )
    
    total_expenses_variance = total_expenses_actual - total_expenses_budgeted
    
    # Calculate net position
    net_budgeted = category_data[CategoryType.INCOME]["budgeted"] - total_expenses_budgeted
    net_actual = category_data[CategoryType.INCOME]["actual"] - total_expenses_actual
    net_variance = net_actual - net_budgeted
    
    # Build response
    return MonthsEndSummary(
        budget_id=budget.id,
        month=month,
        year=year,
        budget_name=budget.name,
        has_budget=True,
        income=CategorySummary(
            budgeted=category_data[CategoryType.INCOME]["budgeted"],
            actual=category_data[CategoryType.INCOME]["actual"],
            variance=income_variance,
            variance_percentage=income_variance_pct
        ),
        expenses=ExpensesSummary(
            total_budgeted=total_expenses_budgeted,
            total_actual=total_expenses_actual,
            total_variance=total_expenses_variance,
            breakdown=ExpenseBreakdown(
                cash=CategorySummary(
                    budgeted=category_data[CategoryType.CASH]["budgeted"],
                    actual=category_data[CategoryType.CASH]["actual"],
                    variance=cash_variance,
                    variance_percentage=cash_variance_pct
                ),
                monthly=CategorySummary(
                    budgeted=category_data[CategoryType.MONTHLY]["budgeted"],
                    actual=category_data[CategoryType.MONTHLY]["actual"],
                    variance=monthly_variance,
                    variance_percentage=monthly_variance_pct
                ),
                savings=CategorySummary(
                    budgeted=category_data[CategoryType.SAVINGS]["budgeted"],
                    actual=category_data[CategoryType.SAVINGS]["actual"],
                    variance=savings_variance,
                    variance_percentage=savings_variance_pct
                )
            )
        ),
        net_position=NetPosition(
            budgeted=net_budgeted,
            actual=net_actual,
            variance=net_variance
        )
    )


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
