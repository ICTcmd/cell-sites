-- Cell Site Mapping & Analytics System - PostgreSQL + PostGIS Schema
-- Requires PostgreSQL 14+ and PostGIS 3.x

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Create custom ENUM types for better data integrity
CREATE TYPE network_type AS ENUM ('2G', '3G', '4G', '5G');
CREATE TYPE band_type AS ENUM ('B1', 'B3', 'B5', 'B7', 'B8', 'B28', 'B41', 'N78', 'UNKNOWN');

-- =============================================================================
-- TABLE: field_logs
-- Purpose: Store raw telemetry data collected from Android devices in the field
-- =============================================================================
CREATE TABLE field_logs (
    id BIGSERIAL PRIMARY KEY,
    
    -- Device & Session Info
    device_id VARCHAR(100) NOT NULL,
    session_id UUID NOT NULL,
    
    -- Cell Network Parameters
    mcc INTEGER NOT NULL CHECK (mcc = 515), -- Philippines
    mnc INTEGER NOT NULL CHECK (mnc IN (3, 5)), -- Smart: 03 (LTE/5G), 05 (Legacy)
    network_type network_type NOT NULL,
    
    -- Cell Tower Identifiers
    enodeb_id INTEGER, -- eNodeB for LTE/5G
    cell_id BIGINT NOT NULL,
    physical_cell_id INTEGER, -- PCI
    tracking_area_code INTEGER, -- TAC
    
    -- Frequency Information
    frequency_band band_type DEFAULT 'UNKNOWN',
    arfcn INTEGER, -- Absolute Radio Frequency Channel Number
    bandwidth_mhz INTEGER,
    
    -- Signal Strength Metrics (dBm)
    rsrp INTEGER CHECK (rsrp BETWEEN -140 AND -40), -- Reference Signal Received Power
    rsrq INTEGER CHECK (rsrq BETWEEN -20 AND -3), -- Reference Signal Received Quality
    rssi INTEGER CHECK (rssi BETWEEN -120 AND -20), -- Received Signal Strength Indicator
    rssnr INTEGER, -- Signal-to-Noise Ratio
    cqi INTEGER CHECK (cqi BETWEEN 0 AND 15), -- Channel Quality Indicator
    
    -- GPS Location Data
    location GEOMETRY(Point, 4326) NOT NULL, -- WGS84 spatial point
    gps_accuracy_meters NUMERIC(8, 2),
    altitude_meters NUMERIC(8, 2),
    
    -- Timing & Metadata
    timestamp_utc TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    device_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Optional Fields
    carrier_name VARCHAR(100),
    connection_status VARCHAR(50),
    notes TEXT,
    
    -- Indexing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Spatial index for fast geographic queries
CREATE INDEX idx_field_logs_location ON field_logs USING GIST (location);

-- Performance indexes
CREATE INDEX idx_field_logs_cell_id ON field_logs (cell_id);
CREATE INDEX idx_field_logs_enodeb_id ON field_logs (enodeb_id) WHERE enodeb_id IS NOT NULL;
CREATE INDEX idx_field_logs_timestamp ON field_logs (timestamp_utc DESC);
CREATE INDEX idx_field_logs_device_session ON field_logs (device_id, session_id);
CREATE INDEX idx_field_logs_network_type ON field_logs (network_type);
CREATE INDEX idx_field_logs_band ON field_logs (frequency_band);

-- =============================================================================
-- TABLE: cell_towers
-- Purpose: Store calculated/estimated tower locations from triangulation
-- =============================================================================
CREATE TABLE cell_towers (
    id SERIAL PRIMARY KEY,
    
    -- Tower Identifiers
    enodeb_id INTEGER UNIQUE NOT NULL,
    site_name VARCHAR(200),
    
    -- Network Info
    mcc INTEGER NOT NULL DEFAULT 515,
    mnc INTEGER NOT NULL CHECK (mnc IN (3, 5)),
    network_type network_type NOT NULL,
    
    -- Estimated Tower Location (calculated via triangulation)
    location GEOMETRY(Point, 4326) NOT NULL,
    
    -- Location Quality Metrics
    confidence_score NUMERIC(5, 2) CHECK (confidence_score BETWEEN 0 AND 100),
    sample_count INTEGER DEFAULT 0, -- Number of field logs used for calculation
    avg_distance_error_meters NUMERIC(10, 2),
    
    -- Data Source
    source VARCHAR(50) DEFAULT 'triangulation', -- 'triangulation', 'opencellid', 'cellmapper', 'manual'
    external_id VARCHAR(100), -- ID from external API if applicable
    
    -- Address & Administrative
    address TEXT,
    barangay VARCHAR(200), -- Philippine administrative division
    city VARCHAR(200),
    province VARCHAR(200),
    
    -- Timing
    first_seen TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE, -- Manually verified location
    notes TEXT
);

-- Spatial index
CREATE INDEX idx_cell_towers_location ON cell_towers USING GIST (location);

-- Performance indexes
CREATE INDEX idx_cell_towers_enodeb ON cell_towers (enodeb_id);
CREATE INDEX idx_cell_towers_network ON cell_towers (network_type);
CREATE INDEX idx_cell_towers_active ON cell_towers (is_active) WHERE is_active = TRUE;

-- =============================================================================
-- TABLE: tower_sectors
-- Purpose: Store individual cell sectors (120° coverage areas) for each tower
-- =============================================================================
CREATE TABLE tower_sectors (
    id SERIAL PRIMARY KEY,
    
    -- Foreign Key to parent tower
    tower_id INTEGER NOT NULL REFERENCES cell_towers(id) ON DELETE CASCADE,
    
    -- Sector Identifiers
    cell_id BIGINT UNIQUE NOT NULL,
    physical_cell_id INTEGER,
    sector_number INTEGER CHECK (sector_number BETWEEN 1 AND 3), -- Typical 3-sector configuration
    
    -- Frequency Information
    frequency_band band_type NOT NULL,
    arfcn INTEGER,
    bandwidth_mhz INTEGER,
    
    -- Sector Orientation
    azimuth_degrees INTEGER CHECK (azimuth_degrees BETWEEN 0 AND 359), -- Direction sector faces
    beamwidth_degrees INTEGER DEFAULT 120 CHECK (beamwidth_degrees BETWEEN 30 AND 180),
    
    -- Coverage Geometry (directional cone/wedge)
    coverage_area GEOMETRY(Polygon, 4326),
    estimated_range_meters INTEGER DEFAULT 1000,
    
    -- Signal Statistics (aggregated from field_logs)
    avg_rsrp NUMERIC(6, 2),
    avg_rssi NUMERIC(6, 2),
    max_observed_distance_meters NUMERIC(10, 2),
    
    -- Metadata
    sample_count INTEGER DEFAULT 0,
    last_observed TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE
);

-- Spatial index
CREATE INDEX idx_tower_sectors_coverage ON tower_sectors USING GIST (coverage_area);

-- Performance indexes
CREATE INDEX idx_tower_sectors_tower_id ON tower_sectors (tower_id);
CREATE INDEX idx_tower_sectors_cell_id ON tower_sectors (cell_id);
CREATE INDEX idx_tower_sectors_band ON tower_sectors (frequency_band);

-- =============================================================================
-- TABLE: external_api_cache
-- Purpose: Cache results from OpenCelliD, CellMapper, etc. to reduce API calls
-- =============================================================================
CREATE TABLE external_api_cache (
    id SERIAL PRIMARY KEY,
    
    api_source VARCHAR(50) NOT NULL, -- 'opencellid', 'cellmapper'
    cell_id BIGINT NOT NULL,
    mcc INTEGER NOT NULL,
    mnc INTEGER NOT NULL,
    
    location GEOMETRY(Point, 4326),
    
    response_data JSONB, -- Store full API response
    
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- Cache expiration
    
    UNIQUE(api_source, cell_id, mcc, mnc)
);

CREATE INDEX idx_api_cache_expires ON external_api_cache (expires_at);
CREATE INDEX idx_api_cache_location ON external_api_cache USING GIST (location);

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to calculate distance between two points in meters
CREATE OR REPLACE FUNCTION calculate_distance_meters(
    point1 GEOMETRY,
    point2 GEOMETRY
) RETURNS NUMERIC AS $$
BEGIN
    RETURN ST_Distance(
        ST_Transform(point1, 3857), -- Transform to Web Mercator for meter calculation
        ST_Transform(point2, 3857)
    );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to create sector coverage polygon
CREATE OR REPLACE FUNCTION create_sector_polygon(
    center_point GEOMETRY,
    azimuth INTEGER,
    beamwidth INTEGER,
    range_meters INTEGER
) RETURNS GEOMETRY AS $$
DECLARE
    start_angle NUMERIC;
    end_angle NUMERIC;
    wedge GEOMETRY;
BEGIN
    start_angle := azimuth - (beamwidth / 2.0);
    end_angle := azimuth + (beamwidth / 2.0);
    
    -- Create a wedge polygon representing the sector coverage
    -- This is a simplified version; production might use more sophisticated propagation models
    wedge := ST_Buffer(
        ST_Project(
            center_point::geography,
            range_meters,
            radians(azimuth)
        )::geometry,
        range_meters * 0.5
    );
    
    RETURN wedge;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- VIEWS FOR ANALYTICS
-- =============================================================================

-- View: Tower summary with sector count and coverage stats
CREATE VIEW v_tower_summary AS
SELECT 
    ct.id,
    ct.enodeb_id,
    ct.site_name,
    ct.network_type,
    ct.location,
    ct.confidence_score,
    ct.sample_count,
    COUNT(ts.id) as sector_count,
    ARRAY_AGG(DISTINCT ts.frequency_band) as active_bands,
    ct.city,
    ct.is_active,
    ct.last_updated
FROM cell_towers ct
LEFT JOIN tower_sectors ts ON ct.id = ts.tower_id
GROUP BY ct.id;

-- View: Recent field observations (last 24 hours)
CREATE VIEW v_recent_observations AS
SELECT 
    fl.id,
    fl.cell_id,
    fl.enodeb_id,
    fl.network_type,
    fl.frequency_band,
    fl.rsrp,
    fl.rssi,
    fl.location,
    fl.timestamp_utc,
    ct.site_name,
    ST_X(fl.location::geometry) as longitude,
    ST_Y(fl.location::geometry) as latitude
FROM field_logs fl
LEFT JOIN cell_towers ct ON fl.enodeb_id = ct.enodeb_id
WHERE fl.timestamp_utc > NOW() - INTERVAL '24 hours'
ORDER BY fl.timestamp_utc DESC;

-- =============================================================================
-- SAMPLE DATA (for testing)
-- =============================================================================

-- Insert a sample tower
INSERT INTO cell_towers (enodeb_id, site_name, network_type, location, confidence_score, source)
VALUES (
    123456,
    'Manila Central Tower',
    '4G',
    ST_SetSRID(ST_MakePoint(121.0244, 14.5995), 4326), -- Manila coordinates
    85.5,
    'manual'
);

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- =============================================================================
-- MAINTENANCE & OPTIMIZATION
-- =============================================================================

-- Vacuum and analyze tables regularly (set up as cron job)
-- VACUUM ANALYZE field_logs;
-- VACUUM ANALYZE cell_towers;
-- VACUUM ANALYZE tower_sectors;

COMMENT ON TABLE field_logs IS 'Raw telemetry data collected from mobile devices';
COMMENT ON TABLE cell_towers IS 'Calculated tower locations from triangulation algorithm';
COMMENT ON TABLE tower_sectors IS 'Individual cell sectors with directional coverage';
COMMENT ON COLUMN field_logs.rsrp IS 'Reference Signal Received Power in dBm (LTE/5G)';
COMMENT ON COLUMN cell_towers.confidence_score IS 'Location accuracy score 0-100 based on sample quality';
