from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum
from decimal import Decimal

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    # Relationships
    budgets: List["Budget"] = Relationship(back_populates="user")
    categories: List["Category"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")

class UserCreate(SQLModel):
    email: str
    name: Optional[str] = None

class UserRead(SQLModel):
    id: int
    email: str
    name: Optional[str] = None
    is_active: bool
    created_at: datetime

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    # Foreign keys
    user_id: int = Field(foreign_key="user.id")
    
    # Relationships
    user: "User" = Relationship(back_populates="categories")
    budget_items: List["BudgetItem"] = Relationship(back_populates="category")

class CategoryCreate(SQLModel):
    name: str

class CategoryRead(SQLModel):
    id: int
    name: str
    is_active: bool

class Budget(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    month: int = Field(index=True)
    year: int = Field(index=True)
    name: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    # Foreign keys
    user_id: int = Field(foreign_key="user.id")
    
    # Relationships
    user: User = Relationship(back_populates="budgets")
    budget_items: List["BudgetItem"] = Relationship(back_populates="budget")

class BudgetCreate(SQLModel):
    month: int
    year: int

class BudgetRead(SQLModel):
    id: int
    month: int
    year: int
    name: str
    is_active: bool
    created_at: datetime

class CategoryType(str, Enum):
    INCOME = "income"
    MONTHLY = "monthly"
    SAVINGS = "savings"
    CASH = "cash"

class BudgetItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: float
    category_type: CategoryType
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    # Foreign keys
    budget_id: int = Field(foreign_key="budget.id")
    category_id: int = Field(foreign_key="category.id")
    
    # Relationships
    budget: Budget = Relationship(back_populates="budget_items")
    category: Category = Relationship(back_populates="budget_items")

class BudgetItemCreate(SQLModel):
    amount: float
    category_type: CategoryType
    category_id: int

class BudgetItemRead(SQLModel):
    id: int
    amount: float
    category_type: CategoryType
    budget_id: int
    category_id: int
    is_active: bool

class AccountType(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    description: Optional[str] = None  # Made optional
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    account_type: AccountType  # Which physical account (checking/savings)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    
    # Foreign keys
    budget_item_id: int = Field(foreign_key="budgetitem.id")
    user_id: int = Field(foreign_key="user.id")
    
    # Relationships
    budget_item: BudgetItem = Relationship()
    user: User = Relationship()

class TransactionCreate(SQLModel):
    amount: Decimal
    description: Optional[str] = None  # Made optional
    transaction_date: Optional[datetime] = None
    budget_item_id: int
    account_type: AccountType  # User explicitly chooses which account

class TransactionRead(SQLModel):
    id: int
    amount: Decimal
    description: Optional[str] = None  # Made optional
    transaction_date: datetime
    account_type: AccountType
    budget_item_id: int
    is_active: bool
    created_at: datetime

class TransactionUpdate(SQLModel):
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    transaction_date: Optional[datetime] = None
    budget_item_id: Optional[int] = None
    account_type: Optional[AccountType] = None