-- Create the timeseries_analytics table if it doesn't exist
CREATE TABLE IF NOT EXISTS timeseries_analytics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    source_id VARCHAR(255) NOT NULL,
    output_img_path TEXT,
    people_ct INTEGER,
    vehicle_ct INTEGER,
    detections JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    analysis_result TEXT
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_timeseries_analytics_timestamp
ON timeseries_analytics(timestamp);

CREATE INDEX IF NOT EXISTS idx_timeseries_analytics_source_id
ON timeseries_analytics(source_id);

-- Insert some sample data if the table is empty
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM timeseries_analytics) = 0 THEN
        INSERT INTO timeseries_analytics (timestamp, source_id, output_img_path, people_ct, vehicle_ct, detections)
        VALUES 
        (NOW() - INTERVAL '1 hour', 'camera-001', 's3://intellibus-hackathon-bucket/detection_test/Screenshot 2025-03-15 at 4.54.39 PM.png', 2, 5, '{"cars": 5, "people": 2}'),
        (NOW() - INTERVAL '2 hours', 'camera-001', 's3://intellibus-hackathon-bucket/detection_test/Screenshot 2025-03-15 at 4.54.39 PM.png', 1, 3, '{"cars": 3, "people": 1}'),
        (NOW() - INTERVAL '3 hours', 'camera-002', 's3://intellibus-hackathon-bucket/detection_test/Screenshot 2025-03-15 at 4.54.39 PM.png', 4, 2, '{"cars": 2, "people": 4}'),
        (NOW() - INTERVAL '4 hours', 'camera-002', 's3://intellibus-hackathon-bucket/detection_test/Screenshot 2025-03-15 at 4.54.39 PM.png', 0, 7, '{"cars": 7, "people": 0}'),
        (NOW() - INTERVAL '5 hours', 'camera-003', 's3://intellibus-hackathon-bucket/detection_test/Screenshot 2025-03-15 at 4.54.39 PM.png', 3, 4, '{"cars": 4, "people": 3}');
    END IF;
END
$$; 