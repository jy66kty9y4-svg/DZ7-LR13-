CREATE TABLE IF NOT EXISTS security_events (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(64),
    ip VARCHAR(64),
    channel VARCHAR(64),
    status VARCHAR(16),
    reason VARCHAR(32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
