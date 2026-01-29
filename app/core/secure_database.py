"""
Secure Database Implementation for Arbify
========================================

Enhanced database security including:
- Field-level encryption
- Audit logging
- Secure backup procedures
- Connection security
"""

import os
import logging
from datetime import datetime
from typing import Any, Optional
from sqlalchemy import event, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from security_config import security_config, DATABASE_SECURITY
from user_models import User, UserProfile, UserArbitrage

# Security logger
security_logger = logging.getLogger("security.database")

class SecureDatabase:
    """Enhanced database security implementation"""
    
    def __init__(self, database_url: str, environment: str = "development"):
        self.database_url = database_url
        self.environment = environment
        self.is_production = environment == "production"
        
        # Setup secure engine
        self.engine = self._create_secure_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Setup audit logging
        self._setup_audit_logging()
    
    def _create_secure_engine(self) -> Engine:
        """Create database engine with security configurations"""
        
        # Base engine configuration
        engine_kwargs = {
            "poolclass": QueuePool,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,  # Verify connections
            "pool_recycle": 3600,   # Recycle connections every hour
        }
        
        # Production-specific security
        if self.is_production:
            engine_kwargs.update({
                "echo": False,  # Don't log SQL in production
                "connect_args": {
                    "sslmode": "require",  # Require SSL for PostgreSQL
                    "application_name": "arbify_secure",
                }
            })
        else:
            # Development configuration
            engine_kwargs.update({
                "echo": False,  # Set to True for SQL debugging
            })
        
        engine = create_engine(self.database_url, **engine_kwargs)
        
        # Add connection event listeners
        self._setup_connection_listeners(engine)
        
        return engine
    
    def _setup_connection_listeners(self, engine: Engine):
        """Setup database connection security listeners"""
        
        @event.listens_for(engine, "connect")
        def set_connection_security(dbapi_connection, connection_record):
            """Set security parameters on each connection"""
            if "postgresql" in self.database_url:
                # PostgreSQL security settings
                with dbapi_connection.cursor() as cursor:
                    # Set statement timeout (prevent long-running queries)
                    cursor.execute("SET statement_timeout = '60s'")
                    
                    # Set timezone to UTC
                    cursor.execute("SET timezone = 'UTC'")
                    
                    # Disable autocommit for explicit transaction control
                    dbapi_connection.autocommit = False
            
            security_logger.info(f"Secure database connection established")
        
        @event.listens_for(engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout for monitoring"""
            connection_record.info['checkout_time'] = datetime.utcnow()
        
        @event.listens_for(engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin and duration"""
            if 'checkout_time' in connection_record.info:
                duration = datetime.utcnow() - connection_record.info['checkout_time']
                if duration.total_seconds() > 30:  # Log long-running connections
                    security_logger.warning(f"Long database connection: {duration.total_seconds()}s")
    
    def _setup_audit_logging(self):
        """Setup audit logging for sensitive operations"""
        
        @event.listens_for(User, 'after_insert')
        def log_user_creation(mapper, connection, target):
            """Log user creation"""
            self._log_audit_event("USER_CREATED", {
                "user_id": target.id,
                "username": target.username,
                "email": target.email,  # This will be encrypted in DB
            })
        
        @event.listens_for(User, 'after_update')
        def log_user_update(mapper, connection, target):
            """Log user updates"""
            self._log_audit_event("USER_UPDATED", {
                "user_id": target.id,
                "username": target.username,
            })
        
        @event.listens_for(UserArbitrage, 'after_insert')
        def log_arbitrage_save(mapper, connection, target):
            """Log arbitrage opportunity saves"""
            self._log_audit_event("ARBITRAGE_SAVED", {
                "user_id": target.user_id,
                "arbitrage_id": target.id,
                "profit_percentage": target.profit_percentage,
            })
    
    def _log_audit_event(self, event_type: str, data: dict):
        """Log audit events"""
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
        }
        security_logger.info(f"AUDIT: {audit_data}")
    
    def get_session(self) -> Session:
        """Get a secure database session"""
        return self.SessionLocal()
    
    def encrypt_field(self, value: str) -> str:
        """Encrypt sensitive field data"""
        if not value:
            return value
        return security_config.encrypt_sensitive_data(value)
    
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt sensitive field data"""
        if not encrypted_value:
            return encrypted_value
        return security_config.decrypt_sensitive_data(encrypted_value)

# Enhanced model mixins for security
class SecureModelMixin:
    """Mixin to add security features to models"""
    
    def encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving"""
        for field in DATABASE_SECURITY["encrypt_fields"]:
            if hasattr(self, field):
                value = getattr(self, field)
                if value and not self._is_encrypted(value):
                    encrypted_value = security_config.encrypt_sensitive_data(str(value))
                    setattr(self, f"_encrypted_{field}", encrypted_value)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields after loading"""
        for field in DATABASE_SECURITY["encrypt_fields"]:
            encrypted_field = f"_encrypted_{field}"
            if hasattr(self, encrypted_field):
                encrypted_value = getattr(self, encrypted_field)
                if encrypted_value:
                    decrypted_value = security_config.decrypt_sensitive_data(encrypted_value)
                    setattr(self, field, decrypted_value)
    
    def _is_encrypted(self, value: str) -> bool:
        """Check if a value is already encrypted"""
        # Simple heuristic: encrypted data typically contains non-printable chars
        try:
            value.encode('ascii')
            return False
        except UnicodeEncodeError:
            return True

class SecureBackupManager:
    """Secure database backup management"""
    
    def __init__(self, database_url: str, backup_encryption_key: Optional[str] = None):
        self.database_url = database_url
        self.backup_key = backup_encryption_key or os.getenv("BACKUP_ENCRYPTION_KEY")
        
        if not self.backup_key:
            security_logger.warning("No backup encryption key provided - backups will be unencrypted!")
    
    def create_secure_backup(self, backup_path: str) -> bool:
        """Create encrypted database backup"""
        try:
            # This is a simplified example - implement based on your database type
            if "postgresql" in self.database_url:
                return self._create_postgres_backup(backup_path)
            elif "sqlite" in self.database_url:
                return self._create_sqlite_backup(backup_path)
            else:
                security_logger.error("Unsupported database type for backup")
                return False
        except Exception as e:
            security_logger.error(f"Backup creation failed: {str(e)}")
            return False
    
    def _create_postgres_backup(self, backup_path: str) -> bool:
        """Create encrypted PostgreSQL backup"""
        import subprocess
        
        try:
            # Use pg_dump with encryption
            cmd = [
                "pg_dump",
                self.database_url,
                "--file", backup_path,
                "--verbose",
                "--compress", "9"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Encrypt the backup file if key is provided
                if self.backup_key:
                    self._encrypt_backup_file(backup_path)
                
                security_logger.info(f"PostgreSQL backup created: {backup_path}")
                return True
            else:
                security_logger.error(f"pg_dump failed: {result.stderr}")
                return False
                
        except Exception as e:
            security_logger.error(f"PostgreSQL backup error: {str(e)}")
            return False
    
    def _create_sqlite_backup(self, backup_path: str) -> bool:
        """Create encrypted SQLite backup"""
        import shutil
        
        try:
            # Extract database file path from URL
            db_file = self.database_url.replace("sqlite:///", "")
            
            # Copy database file
            shutil.copy2(db_file, backup_path)
            
            # Encrypt the backup if key is provided
            if self.backup_key:
                self._encrypt_backup_file(backup_path)
            
            security_logger.info(f"SQLite backup created: {backup_path}")
            return True
            
        except Exception as e:
            security_logger.error(f"SQLite backup error: {str(e)}")
            return False
    
    def _encrypt_backup_file(self, file_path: str):
        """Encrypt backup file"""
        try:
            from cryptography.fernet import Fernet
            
            # Initialize cipher
            if isinstance(self.backup_key, str):
                key = self.backup_key.encode()
            else:
                key = self.backup_key
                
            cipher = Fernet(key)
            
            # Read and encrypt file
            with open(file_path, 'rb') as f:
                data = f.read()
            
            encrypted_data = cipher.encrypt(data)
            
            # Write encrypted data back
            with open(f"{file_path}.encrypted", 'wb') as f:
                f.write(encrypted_data)
            
            # Remove unencrypted file
            os.remove(file_path)
            os.rename(f"{file_path}.encrypted", file_path)
            
            security_logger.info(f"Backup file encrypted: {file_path}")
            
        except Exception as e:
            security_logger.error(f"Backup encryption failed: {str(e)}")

# Initialize secure database
def get_secure_database(database_url: str, environment: str = "development") -> SecureDatabase:
    """Get secure database instance"""
    return SecureDatabase(database_url, environment)

# Export classes and functions
__all__ = [
    'SecureDatabase', 
    'SecureModelMixin', 
    'SecureBackupManager',
    'get_secure_database'
]
