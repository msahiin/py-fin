-- TimescaleDB Initialization Script
-- Creates hypertables for time-series data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create market_data hypertable (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'market_data') THEN
        CREATE TABLE market_data (
            time TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume DOUBLE PRECISION,
            PRIMARY KEY (time, symbol)
        );

        -- Convert to hypertable
        SELECT create_hypertable('market_data', 'time');

        -- Create indexes
        CREATE INDEX ON market_data (symbol, time DESC);

        RAISE NOTICE 'market_data hypertable created';
    END IF;
END $$;

-- Create price_ticks table for real-time price updates
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'price_ticks') THEN
        CREATE TABLE price_ticks (
            time TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            volume DOUBLE PRECISION,
            PRIMARY KEY (time, symbol)
        );

        SELECT create_hypertable('price_ticks', 'time');

        CREATE INDEX ON price_ticks (symbol, time DESC);

        RAISE NOTICE 'price_ticks hypertable created';
    END IF;
END $$;

-- Enable compression for older data (optional)
SELECT add_compression_policy('market_data', INTERVAL '7 days');
SELECT add_compression_policy('price_ticks', INTERVAL '1 day');

-- Create continuous aggregates for common queries (optional)
CREATE MATERIALIZED VIEW IF NOT EXISTS market_data_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    symbol,
    first(open, time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, time) AS close,
    sum(volume) AS volume
FROM market_data
GROUP BY bucket, symbol
WITH NO DATA;

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('market_data_1h',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

RAISE NOTICE 'TimescaleDB initialization complete';
