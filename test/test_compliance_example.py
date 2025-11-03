"""
Test file with intentional security/compliance issues
This demonstrates what Code Indexer can detect
"""

# ❌ VIOLATION 1: Hardcoded credentials
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "admin123"

# ❌ VIOLATION 2: Custom authentication (should use centralized service)
def custom_login(username, password):
    if password == "admin":
        return {"user": username, "token": "abc123"}
    return None

# ❌ VIOLATION 3: SQL injection vulnerability
def get_user_data(user_id):
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    return execute_query(query)

# ❌ VIOLATION 4: Missing error handling
def process_payment(amount):
    charge_card(amount)
    update_balance(amount)
    return "success"

# ❌ VIOLATION 5: Logging sensitive data
def create_account(username, password, ssn):
    logger.info(f"Creating account: {username}, password: {password}, SSN: {ssn}")
    return save_user(username, password, ssn)

# ❌ VIOLATION 6: No input validation
def update_profile(request):
    data = request.json
    db.users.update({"id": data["user_id"]}, data)
    return "updated"

# ❌ VIOLATION 7: Missing authentication check
def delete_user(user_id):
    db.users.delete({"id": user_id})
    return "deleted"

def execute_query(query):
    pass

def charge_card(amount):
    pass

def update_balance(amount):
    pass

def save_user(username, password, ssn):
    pass

class logger:
    @staticmethod
    def info(msg):
        print(msg)

class db:
    class users:
        @staticmethod
        def update(filter, data):
            pass
        
        @staticmethod
        def delete(filter):
            pass
