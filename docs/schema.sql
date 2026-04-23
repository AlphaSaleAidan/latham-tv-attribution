-- Latham Pools TV Attribution Platform
-- Supabase PostgreSQL Schema
-- Run this in the Supabase SQL Editor to set up all tables

-- =============================================
-- 1. TV Airings — the trigger events
-- =============================================
CREATE TABLE IF NOT EXISTS tv_airings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    airing_timestamp TIMESTAMPTZ NOT NULL,
    network TEXT NOT NULL,
    dma_code TEXT,
    dma_name TEXT,
    creative_id TEXT,
    creative_name TEXT,
    duration_seconds INTEGER,
    estimated_impressions BIGINT,
    spend DECIMAL(12, 2),
    daypart TEXT,
    program_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_airings_timestamp ON tv_airings(airing_timestamp DESC);
CREATE INDEX idx_airings_network ON tv_airings(network);
CREATE INDEX idx_airings_dma ON tv_airings(dma_code);
CREATE INDEX idx_airings_creative ON tv_airings(creative_id);

-- =============================================
-- 2. Google Trends Data — brand lift signal
-- =============================================
CREATE TABLE IF NOT EXISTS trends_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL,
    search_term TEXT NOT NULL,
    interest_score INTEGER NOT NULL CHECK (interest_score >= 0 AND interest_score <= 100),
    geo TEXT DEFAULT 'US',
    is_partial BOOLEAN DEFAULT FALSE,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, search_term, geo)
);

CREATE INDEX idx_trends_timestamp ON trends_data(timestamp DESC);
CREATE INDEX idx_trends_term ON trends_data(search_term);
CREATE INDEX idx_trends_geo ON trends_data(geo);

-- =============================================
-- 3. GA4 Analytics Data — web traffic signal
-- =============================================
CREATE TABLE IF NOT EXISTS ga4_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL,
    metric_name TEXT NOT NULL, -- 'sessions', 'activeUsers', 'conversions', 'newUsers'
    value DECIMAL(12, 2) NOT NULL,
    dimension_city TEXT,
    dimension_region TEXT,
    dimension_source TEXT,
    dimension_medium TEXT,
    dimension_landing_page TEXT,
    fetched_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ga4_timestamp ON ga4_data(timestamp DESC);
CREATE INDEX idx_ga4_metric ON ga4_data(metric_name);
CREATE INDEX idx_ga4_region ON ga4_data(dimension_region);

-- =============================================
-- 4. Search Console Data — organic search signal
-- =============================================
CREATE TABLE IF NOT EXISTS search_console_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    query TEXT NOT NULL,
    page TEXT,
    clicks INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    ctr DECIMAL(6, 4),
    position DECIMAL(6, 2),
    country TEXT DEFAULT 'USA',
    device TEXT, -- 'DESKTOP', 'MOBILE', 'TABLET'
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date, query, page, country, device)
);

CREATE INDEX idx_gsc_date ON search_console_data(date DESC);
CREATE INDEX idx_gsc_query ON search_console_data(query);

-- =============================================
-- 5. Call Tracking Data
-- =============================================
CREATE TABLE IF NOT EXISTS call_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    call_timestamp TIMESTAMPTZ NOT NULL,
    caller_city TEXT,
    caller_state TEXT,
    caller_zip TEXT,
    duration_seconds INTEGER,
    tracking_number TEXT,
    campaign_name TEXT,
    is_first_call BOOLEAN DEFAULT FALSE,
    call_source TEXT, -- 'organic', 'direct', 'tv', etc.
    fetched_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_calls_timestamp ON call_data(call_timestamp DESC);
CREATE INDEX idx_calls_state ON call_data(caller_state);

-- =============================================
-- 6. QR Code Scan Data
-- =============================================
CREATE TABLE IF NOT EXISTS qr_scan_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_timestamp TIMESTAMPTZ NOT NULL,
    scan_city TEXT,
    scan_region TEXT,
    scan_country TEXT DEFAULT 'US',
    device_type TEXT,
    qr_code_id TEXT,
    campaign_name TEXT,
    destination_url TEXT,
    fetched_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_qr_timestamp ON qr_scan_data(scan_timestamp DESC);
CREATE INDEX idx_qr_region ON qr_scan_data(scan_region);

-- =============================================
-- 7. Correlation Results — computed attribution
-- =============================================
CREATE TABLE IF NOT EXISTS correlation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    airing_id UUID REFERENCES tv_airings(id),
    airing_timestamp TIMESTAMPTZ NOT NULL,
    network TEXT,
    dma_code TEXT,
    creative_id TEXT,

    -- Lift metrics by time window (JSON: {"immediate": 15.2, "short": 8.1, ...})
    trends_lift JSONB DEFAULT '{}',
    ga4_session_lift JSONB DEFAULT '{}',
    ga4_conversion_lift JSONB DEFAULT '{}',
    search_console_lift JSONB DEFAULT '{}',
    call_volume_lift JSONB DEFAULT '{}',
    qr_scan_lift JSONB DEFAULT '{}',

    -- Composite metrics
    composite_score DECIMAL(6, 2),
    confidence DECIMAL(4, 3),
    signals_available INTEGER DEFAULT 0,
    is_significant BOOLEAN DEFAULT FALSE,

    analyzed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_corr_airing ON correlation_results(airing_id);
CREATE INDEX idx_corr_timestamp ON correlation_results(airing_timestamp DESC);
CREATE INDEX idx_corr_network ON correlation_results(network);
CREATE INDEX idx_corr_significant ON correlation_results(is_significant) WHERE is_significant = TRUE;

-- =============================================
-- 8. Campaign Summaries — aggregated reports
-- =============================================
CREATE TABLE IF NOT EXISTS campaign_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    group_by TEXT NOT NULL, -- 'network', 'creative', 'dma', 'overall'
    group_value TEXT NOT NULL,

    total_airings INTEGER DEFAULT 0,
    total_spend DECIMAL(12, 2) DEFAULT 0,
    total_impressions BIGINT DEFAULT 0,

    avg_trends_lift DECIMAL(8, 2),
    avg_session_lift DECIMAL(8, 2),
    avg_conversion_lift DECIMAL(8, 2),
    avg_call_lift DECIMAL(8, 2),
    avg_composite_score DECIMAL(6, 2),

    significant_airings INTEGER DEFAULT 0,
    significance_rate DECIMAL(6, 2),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(period_start, period_end, group_by, group_value)
);

-- =============================================
-- Row Level Security (RLS)
-- =============================================
-- For now, disable RLS since we're using service role key
-- Enable and configure when adding user authentication

ALTER TABLE tv_airings ENABLE ROW LEVEL SECURITY;
ALTER TABLE trends_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE ga4_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_console_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE qr_scan_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE correlation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_summaries ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Service role full access" ON tv_airings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON trends_data FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON ga4_data FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON search_console_data FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON call_data FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON qr_scan_data FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON correlation_results FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service role full access" ON campaign_summaries FOR ALL USING (true) WITH CHECK (true);
