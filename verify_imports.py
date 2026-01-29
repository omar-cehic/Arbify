
import sys
import os
import traceback

# Add root to path
sys.path.append(os.getcwd())

print(f"CWD: {os.getcwd()}")
print(f"Sys Path: {sys.path}")

try:
    print("Testing imports...")
    
    print("Importing app.core.config...")
    from app.core import config
    print("✅ app.core.config imported")

    print("Importing app.core.database...")
    from app.core import database
    print("✅ app.core.database imported")

    print("Importing app.models.user...")
    from app.models import user
    print("✅ app.models.user imported")

    print("Importing app.api.v1.auth...")
    from app.api.v1 import auth
    print("✅ app.api.v1.auth imported")

    print("Importing app.api.v1.users...")
    from app.api.v1 import users
    print("✅ app.api.v1.users imported")

    print("Importing app.api.v1.router...")
    from app.api.v1 import router
    print("✅ app.api.v1.router imported")

    print("Importing app.main...")
    from app import main
    print("✅ app.main imported")
    
    print("All imports verified!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    traceback.print_exc()
