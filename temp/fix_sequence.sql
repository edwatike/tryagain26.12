-- Fix permissions on domains_queue_id_seq sequence
GRANT ALL PRIVILEGES ON SEQUENCE domains_queue_id_seq TO postgres;
GRANT ALL PRIVILEGES ON SEQUENCE domains_queue_id_seq TO PUBLIC;
ALTER SEQUENCE domains_queue_id_seq OWNER TO postgres;







