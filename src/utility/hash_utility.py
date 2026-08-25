import bcrypt
import hashlib

def hash_password(password: str):
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str):
    try:
        # Handle both direct bcrypt and passlib-generated hashes
        plain_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        result = bcrypt.checkpw(plain_bytes, hashed_bytes)
        return result
    except Exception as e:
        print(f"🔍 DEBUG: Password verification error: {e}")
        return False

        