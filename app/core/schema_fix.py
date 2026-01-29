from sqlalchemy import text
from app.core.database import SessionLocal
import logging

logger = logging.getLogger(__name__)

def check_and_fix_schema():
    """
    Checks if critical columns exist in 'user_arbitrage_history' table
    and adds them if missing. This ensures the DB matches the model.
    """
    db = SessionLocal()
    try:
        # Define expected columns and their types (PostgreSQL compatible)
        # Dictionary format: column_name: sql_type_definition
        expected_columns = {
            "sport_title": "VARCHAR",
            "commence_time": "TIMESTAMP",
            "winning_outcome": "VARCHAR",
            "profit_percentage": "FLOAT",
            "bet_amount": "FLOAT DEFAULT 0.0",
            "profit": "FLOAT DEFAULT 0.0",
            "odds": "JSON DEFAULT '{}'"
        }
        
        # Get existing columns
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='user_arbitrage_history';
        """)
        result = db.execute(check_query).fetchall()
        existing_columns = [row[0] for row in result]
        
        logger.info(f"🔍 Existing columns in user_arbitrage_history: {existing_columns}")
        
        changes_made = False
        for col_name, col_type in expected_columns.items():
            if col_name not in existing_columns:
                logger.warning(f"⚠️ Column '{col_name}' missing. Adding it...")
                try:
                    alter_query = text(f"ALTER TABLE user_arbitrage_history ADD COLUMN IF NOT EXISTS {col_name} {col_type};")
                    db.execute(alter_query)
                    changes_made = True
                    logger.info(f"✅ Added '{col_name}'")
                except Exception as e:
                    logger.error(f"❌ Failed to add '{col_name}': {e}")
        
        if changes_made:
            db.commit()
            logger.info("✅ Schema repair completed.")
        else:
            logger.info("✅ Schema matches expectations (no repairs needed).")
            
    except Exception as e:
        logger.error(f"❌ Failed to check/fix schema: {str(e)}")
        db.rollback()
    finally:
        db.close()
