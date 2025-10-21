from sqlmodel import Session, select
from app.models import User, Category

def create_default_categories(session: Session, user_id: int) -> None:
    """
    Create a simple list of default categories for a new user.
    """
    existing_categories = session.exec(
        select(Category).where(Category.user_id == user_id)
    ).first()
    
    if existing_categories:
        return

    default_category_names = [
        # Income
        "Salary", "Freelance", "Investments", "Other Income",
        # Savings
        "Emergency Fund", "Retirement", "Vacation", "Major Purchase",
        # Monthly Bills
        "Rent/Mortgage", "Utilities", "Internet/Phone", "Insurance", "Subscriptions",
        # Common Expenses
        "Groceries", "Dining Out", "Entertainment", "Transportation", "Shopping",
        "Personal Care", "Gifts", "Miscellaneous"
    ]

    for name in default_category_names:
        category = Category(name=name, user_id=user_id)
        session.add(category)
        
    session.commit()