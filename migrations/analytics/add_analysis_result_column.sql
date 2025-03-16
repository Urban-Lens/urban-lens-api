-- Add analysis_result column to the timeseries_analytics table
-- This column will store the results of the Gemini API image analysis

-- First check if the column already exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'timeseries_analytics'
        AND column_name = 'analysis_result'
    ) THEN
        -- Add the analysis_result column
        ALTER TABLE timeseries_analytics
        ADD COLUMN analysis_result TEXT;
        
        -- Add an index on the source_id column for faster queries
        CREATE INDEX IF NOT EXISTS idx_timeseries_analytics_source_id
        ON timeseries_analytics(source_id);
        
        -- Add an index on the timestamp column for faster time-based queries
        CREATE INDEX IF NOT EXISTS idx_timeseries_analytics_timestamp
        ON timeseries_analytics(timestamp);
    END IF;
END
$$; 