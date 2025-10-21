from sqlmodel import Session, select
from app.models import User, Category, CategoryType

def create_default_categories(session: Session, user_id: int) -> None:
    """
    Create default categories for a new user
    """
    # Check if the user already has categories
    existing_categories = session.exec(
        select(Category).where(Category.user_id == user_id)
    ).all()
    
    if existing_categories:
        # User already has categories, no need to create defaults
        return
    
    # Default income categories
    income_categories = [
        Category(
            name="Salary",
            type=CategoryType.INCOME,
            description="Regular employment income",
            user_id=user_id
        ),
        Category(
            name="Freelance",
            type=CategoryType.INCOME,
            description="Income from freelance work",
            user_id=user_id
        ),
        Category(
            name="Investments",
            type=CategoryType.INCOME,
            description="Income from investments",
            user_id=user_id
        ),
        Category(
            name="Other Income",
            type=CategoryType.INCOME,
            description="Other sources of income",
            user_id=user_id
        )
    ]
    
    # Default savings categories
    savings_categories = [
        Category(
            name="Emergency Fund",
            type=CategoryType.SAVINGS,
            description="Savings for emergencies",
            user_id=user_id
        ),
        Category(
            name="Retirement",
            type=CategoryType.SAVINGS,
            description="Retirement savings",
            user_id=user_id
        ),
        Category(
            name="Vacation",
            type=CategoryType.SAVINGS,
            description="Savings for vacations",
            user_id=user_id
        ),
        Category(
            name="Major Purchase",
            type=CategoryType.SAVINGS,
            description="Savings for major purchases",
            user_id=user_id
        )
    ]
    
    # Default monthly expense categories
    monthly_categories = [
        Category(
            name="Rent/Mortgage",
            type=CategoryType.MONTHLY,
            description="Housing expenses",
            user_id=user_id
        ),
        Category(
            name="Utilities",
            type=CategoryType.MONTHLY,
            description="Electricity, water, gas, etc.",
            user_id=user_id
        ),
        Category(
            name="Internet/Phone",
            type=CategoryType.MONTHLY,
            description="Internet and phone bills",
            user_id=user_id
        ),
        Category(
            name="Insurance",
            type=CategoryType.MONTHLY,
            description="Health, auto, home insurance",
            user_id=user_id
        ),
        Category(
            name="Subscriptions",
            type=CategoryType.MONTHLY,
            description="Streaming services, memberships",
            user_id=user_id
        )
    ]
    
    # Default cash expense categories
    cash_categories = [
        Category(
            name="Groceries",
            type=CategoryType.CASH,
            description="Food and household items",
            user_id=user_id
        ),
        Category(
            name="Dining Out",
            type=CategoryType.CASH,
            description="Restaurants and takeout",
            user_id=user_id
        ),
        Category(
            name="Entertainment",
            type=CategoryType.CASH,
            description="Movies, events, hobbies",
            user_id=user_id
        ),
        Category(
            name="Transportation",
            type=CategoryType.CASH,
            description="Gas, public transit, rideshare",
            user_id=user_id
        ),
        Category(
            name="Shopping",
            type=CategoryType.CASH,
            description="Clothing, electronics, etc.",
            user_id=user_id
        ),
        Category(
            name="Personal Care",
            type=CategoryType.CASH,
            description="Haircuts, gym, etc.",
            user_id=user_id
        ),
        Category(
            name="Gifts",
            type=CategoryType.CASH,
            description="Gifts for others",
            user_id=user_id
        ),
        Category(
            name="Miscellaneous",
            type=CategoryType.CASH,
            description="Other expenses",
            user_id=user_id
        )
    ]
    
    # Add all categories to the session
    for category in income_categories + savings_categories + monthly_categories + cash_categories:
        session.add(category)
    
    # Commit the changes
    session.commit()