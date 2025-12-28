-- Fix sequence name issue: rename domains_queue_new_id_seq to domains_queue_id_seq
-- This ensures the sequence name matches what SQLAlchemy expects

-- First, check if domains_queue_new_id_seq exists and rename it
DO $$
BEGIN
    -- Check if domains_queue_new_id_seq exists
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE sequencename = 'domains_queue_new_id_seq') THEN
        -- Rename to standard name
        ALTER SEQUENCE domains_queue_new_id_seq RENAME TO domains_queue_id_seq;
        RAISE NOTICE 'Renamed domains_queue_new_id_seq to domains_queue_id_seq';
    END IF;
    
    -- Grant permissions on the correct sequence
    GRANT ALL PRIVILEGES ON SEQUENCE domains_queue_id_seq TO postgres;
    GRANT ALL PRIVILEGES ON SEQUENCE domains_queue_id_seq TO PUBLIC;
    ALTER SEQUENCE domains_queue_id_seq OWNER TO postgres;
    RAISE NOTICE 'Granted permissions on domains_queue_id_seq';
END $$;

