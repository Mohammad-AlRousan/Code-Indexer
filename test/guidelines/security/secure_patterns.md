# Security Patterns and Best Practices

## ✅ Authentication Best Practices

### Always use centralized authentication service
```python
from auth.service import AuthService

def protected_endpoint(request):
    user = AuthService.verify_token(request.headers['Authorization'])
    if not user:
        raise Unauthorized()
    # Continue with authorized logic
```

### Never hardcode credentials
```python
# ❌ WRONG
API_KEY = "sk-1234567890"

# ✅ CORRECT
import os
API_KEY = os.getenv('API_KEY')
```

## ✅ Input Validation

### Always validate and sanitize user input
```python
from schemas import UserSchema
from exceptions import ValidationError

def update_profile(request):
    try:
        data = UserSchema.validate(request.json)
        user = db.users.update(data)
        return user
    except ValidationError as e:
        return {"error": str(e)}, 400
```

## ✅ SQL Security

### Use parameterized queries
```python
# ❌ WRONG - SQL Injection risk
query = "SELECT * FROM users WHERE id = '" + user_id + "'"

# ✅ CORRECT - Parameterized query
query = "SELECT * FROM users WHERE id = ?"
cursor.execute(query, (user_id,))
```

## ✅ Error Handling

### Always wrap operations in try/except
```python
def process_payment(amount):
    try:
        charge_card(amount)
        update_balance(amount)
        logger.info(f"Payment processed: {amount}")
        return {"status": "success"}
    except PaymentError as e:
        logger.error(f"Payment failed: {e}")
        return {"status": "error", "message": str(e)}, 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {"status": "error"}, 500
```

## ✅ Logging Security

### Never log sensitive data
```python
# ❌ WRONG
logger.info(f"User login: {username}, password: {password}")

# ✅ CORRECT
logger.info(f"User login: {username}")
```

## Required Security Checks

- No hardcoded credentials (use environment variables)
- All endpoints must authenticate users
- All user input must be validated
- Use parameterized SQL queries
- Proper error handling with try/except
- Never log PII or sensitive data
- Session tokens must expire
- Passwords must be hashed (bcrypt, min 12 rounds)
