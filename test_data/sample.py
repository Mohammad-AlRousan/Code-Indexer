"""
Sample Python module for testing the code indexer
"""

def calculate_total(items: list) -> float:
    """Calculate total price of items"""
    total = 0.0
    for item in items:
        total += item.price * item.quantity
    return total


def validate_email(email: str) -> bool:
    """Validate email address format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


class ShoppingCart:
    """Shopping cart implementation"""
    
    def __init__(self):
        self.items = []
    
    def add_item(self, item, quantity: int = 1):
        """Add item to cart"""
        self.items.append({'item': item, 'quantity': quantity})
    
    def get_total(self) -> float:
        """Calculate cart total"""
        return sum(item['item'].price * item['quantity'] for item in self.items)
    
    def clear(self):
        """Clear all items from cart"""
        self.items = []


async def fetch_user_data(user_id: int):
    """Fetch user data from API"""
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.example.com/users/{user_id}') as response:
            return await response.json()
