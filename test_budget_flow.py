import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API base URL
BASE_URL = "http://localhost:8000"

def test_budget_creation_flow():
    """Test the complete budget creation flow"""
    
    # Step 1: Request a magic link
    logger.info("Step 1: Requesting a magic link")
    email = "test@example.com"
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email}
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to request magic link: {response.text}")
        return
    
    logger.info("Magic link requested successfully")
    
    # Step 2: Check the server logs for the magic link token
    logger.info("Step 2: Please check the server logs for the magic link token")
    token = input("Enter the token from the magic link: ")
    
    # Step 3: Verify the token
    logger.info("Step 3: Verifying the token")
    response = requests.post(
        f"{BASE_URL}/api/auth/verify",
        json={"token": token}
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to verify token: {response.text}")
        return
    
    access_token = response.json().get("access_token")
    logger.info("Token verified successfully, received access token")
    
    # Step 4: Get user info
    logger.info("Step 4: Getting user info")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        f"{BASE_URL}/api/users/me",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get user info: {response.text}")
        return
    
    user = response.json()
    logger.info(f"User info retrieved: {user}")
    
    # Step 5: Get categories
    logger.info("Step 5: Getting categories")
    response = requests.get(
        f"{BASE_URL}/api/budgets/categories",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get categories: {response.text}")
        return
    
    categories = response.json()
    logger.info(f"Retrieved {len(categories)} categories")
    
    # Step 6: Create a budget
    logger.info("Step 6: Creating a budget")
    current_month = 10  # October
    current_year = 2025
    
    budget_data = {
        "month": current_month,
        "year": current_year,
        "name": f"Budget for October 2025",
        "description": "Test budget"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/budgets",
        json=budget_data,
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to create budget: {response.text}")
        return
    
    budget = response.json()
    logger.info(f"Budget created: {budget}")
    
    # Step 7: Add budget items
    logger.info("Step 7: Adding budget items")
    
    # Find an income category
    income_category = next((c for c in categories if c["type"] == "income"), None)
    if income_category:
        budget_item = {
            "budget_id": budget["id"],
            "category_id": income_category["id"],
            "amount": 5000.00
        }
        
        response = requests.post(
            f"{BASE_URL}/api/budgets/items",
            json=budget_item,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to add income budget item: {response.text}")
        else:
            logger.info(f"Added income budget item: {response.json()}")
    
    # Find a savings category
    savings_category = next((c for c in categories if c["type"] == "savings"), None)
    if savings_category:
        budget_item = {
            "budget_id": budget["id"],
            "category_id": savings_category["id"],
            "amount": 1000.00
        }
        
        response = requests.post(
            f"{BASE_URL}/api/budgets/items",
            json=budget_item,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to add savings budget item: {response.text}")
        else:
            logger.info(f"Added savings budget item: {response.json()}")
    
    # Find a monthly category
    monthly_category = next((c for c in categories if c["type"] == "monthly"), None)
    if monthly_category:
        budget_item = {
            "budget_id": budget["id"],
            "category_id": monthly_category["id"],
            "amount": 1500.00
        }
        
        response = requests.post(
            f"{BASE_URL}/api/budgets/items",
            json=budget_item,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to add monthly budget item: {response.text}")
        else:
            logger.info(f"Added monthly budget item: {response.json()}")
    
    # Find a cash category
    cash_category = next((c for c in categories if c["type"] == "cash"), None)
    if cash_category:
        budget_item = {
            "budget_id": budget["id"],
            "category_id": cash_category["id"],
            "amount": 800.00
        }
        
        response = requests.post(
            f"{BASE_URL}/api/budgets/items",
            json=budget_item,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to add cash budget item: {response.text}")
        else:
            logger.info(f"Added cash budget item: {response.json()}")
    
    # Step 8: Get budget items
    logger.info("Step 8: Getting budget items")
    response = requests.get(
        f"{BASE_URL}/api/budgets/items/{budget['id']}",
        headers=headers
    )
    
    if response.status_code != 200:
        logger.error(f"Failed to get budget items: {response.text}")
        return
    
    budget_items = response.json()
    logger.info(f"Retrieved {len(budget_items)} budget items")
    
    # Test complete
    logger.info("Budget creation flow test completed successfully!")

if __name__ == "__main__":
    test_budget_creation_flow()