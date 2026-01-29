from passlib.context import CryptContext
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", ".*bcrypt.*", module="passlib")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    print(f"Hashing password of length {len(password)}")
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        print("Truncating password > 72 bytes")
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    print(f"Verifying password of length {len(plain)}")
    plain_bytes = plain.encode('utf-8')
    if len(plain_bytes) > 72:
        print("Truncating verification password > 72 bytes")
        plain = plain_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(plain, hashed)

# Test long password
long_pass = "a" * 100
print(f"Long password length: {len(long_pass)}")

try:
    hashed = hash_password(long_pass)
    print(f"Hashed successfully: {hashed[:20]}...")
    
    is_valid = verify_password(long_pass, hashed)
    print(f"Verification result: {is_valid}")
    
    assert is_valid == True
    print("✅ TEST PASSED")
except Exception as e:
    print(f"❌ TEST FAILED: {e}")
