-- Emergency fix for missing odds_format column
-- Run this in Railway Database Console

-- Add the missing column (safe operation - won't fail if exists)
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_profiles' 
        AND column_name = 'odds_format'
    ) THEN
        ALTER TABLE user_profiles ADD COLUMN odds_format VARCHAR(20) DEFAULT 'decimal';
        
        -- Update existing rows
        UPDATE user_profiles SET odds_format = 'decimal' WHERE odds_format IS NULL;
        
        -- Log success
        RAISE NOTICE 'Successfully added odds_format column';
    ELSE
        RAISE NOTICE 'odds_format column already exists';
    END IF;
END $$;
