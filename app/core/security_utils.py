from passlib.context import CryptContext
import hashlib
import os
import warnings
from dotenv import load_dotenv

# Suppress passlib bcrypt version warnings globally
warnings.filterwarnings("ignore", ".*bcrypt.*", module="passlib")
warnings.filterwarnings("ignore", ".*__about__.*", module="passlib")

load_dotenv()

# Avoid circular imports by checking environment directly
DEV_MODE = os.getenv("ENVIRONMENT", "development") == "development"

# Create password context with bcrypt - handle version compatibility issues

try:
    # Try creating context normally first
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception as e:
    print(f"⚠️ Bcrypt context creation failed: {str(e)}")
    try:
        # Fallback: Create context with explicit settings
        pwd_context = CryptContext(
            schemes=["bcrypt"], 
            deprecated="auto",
            bcrypt__rounds=12,
            bcrypt__default_rounds=12
        )
    except Exception as e2:
        print(f"⚠️ Fallback bcrypt failed: {str(e2)}")
        # Ultimate fallback: Create a simple context
        pwd_context = CryptContext(schemes=["bcrypt"])

# Legacy secret key for backward compatibility - use the original hardcoded key
LEGACY_SECRET_KEY = "arbitragesecretkey123456789"

def hash_password(password: str) -> str:
    """Create a secure hash of the password using bcrypt"""
    # Truncate to 72 bytes to avoid bcrypt limitation
    # This is a known limitation of bcrypt. We truncate the bytes, not characters.
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)

def verify_legacy_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against legacy SHA-256 hash"""
    try:
        # Recreate the old hashing method
        salted = plain_password + LEGACY_SECRET_KEY
        test_hash = hashlib.sha256(salted.encode()).hexdigest()
        return test_hash == hashed_password
    except Exception:
        return False

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash (supports both bcrypt and legacy SHA-256)"""
    
    if DEV_MODE:
        print(f"🔍 Password verification debug:")
        print(f"  - Password length: {len(plain_password)}")
        print(f"  - Hash format: {'bcrypt' if hashed_password.startswith('$2b$') else 'legacy-sha256'}")
        print(f"  - Hash preview: {hashed_password[:20]}...")
    
    # Suppress bcrypt warnings during verification
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        
        # Try direct bcrypt first for bcrypt hashes
        if hashed_password.startswith('$2b$') or hashed_password.startswith('$2a$'):
            try:
                import bcrypt
                # Truncate to 72 bytes to match hashing logic
                plain_bytes = plain_password.encode('utf-8')
                if len(plain_bytes) > 72:
                    plain_bytes = plain_bytes[:72]
                
                result = bcrypt.checkpw(plain_bytes, hashed_password.encode('utf-8'))
                if DEV_MODE:
                    print(f"  - Direct bcrypt result: {result}")
                return result
            except Exception as bcrypt_e:
                if DEV_MODE:
                    print(f"  - Direct bcrypt failed: {str(bcrypt_e)}")
        
        # Try passlib context verification
        try:
            result = pwd_context.verify(plain_password, hashed_password)
            if DEV_MODE:
                print(f"  - Passlib result: {result}")
            return result
        except Exception as e:
            if DEV_MODE:
                print(f"  - Passlib failed: {str(e)}")
        
        # If everything fails, try legacy SHA-256 verification
        legacy_result = verify_legacy_password(plain_password, hashed_password)
        if DEV_MODE:
            print(f"  - Legacy result: {legacy_result}")
        return legacy_result