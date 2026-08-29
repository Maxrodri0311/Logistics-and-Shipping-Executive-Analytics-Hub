-- =============================================================================
-- Logistics KPI Automation & Multi-Carrier Analytics Platform
-- Module: Tableau & Looker Studio Analytical Semantic Views (tableau_looker_views.sql)
--
-- Provides flat, pre-joined dimensional models optimized for single-pass ingestion
-- in Tableau Hyper extracts and Looker Studio / BigQuery / DuckDB connectors.
-- =============================================================================

-- 1. TABLEAU MASTER LOGISTICS EXTRACT (Single Table Semantic Flat Model)
CREATE OR REPLACE VIEW v_tableau_shipment_extract AS
SELECT 
    -- Shipment Core Attributes
    s.shipment_id,
    s.tracking_number,
    s.order_date_id,
    CAST(s.order_timestamp AS DATE) AS order_date,
    s.promised_delivery_date_id,
    s.actual_delivery_date_id,
    CAST(s.actual_delivery_timestamp AS DATE) AS actual_delivery_date,
    s.service_level,
    s.delivery_status,
    s.declared_weight_kg,
    s.billed_weight_kg,
    s.is_weight_discrepancy,
    
    -- Financials & Margin
    s.quoted_shipping_fee,
    s.billed_carrier_cost,
    s.carrier_cost_variance,
    s.gross_revenue,
    s.net_margin,
    s.net_margin_pct,
    
    -- SLA Performance
    s.transit_time_days,
    s.promised_sla_days,
    s.is_sla_breached,
    s.is_exception,
    CASE WHEN s.is_sla_breached = 0 THEN 'On-Time' ELSE 'SLA Breached' END AS otd_status,
    
    -- Carrier Dimension
    c.carrier_id,
    c.carrier_name,
    c.carrier_code,
    c.contract_tier AS carrier_contract_tier,
    c.base_sla_days AS carrier_base_sla,
    c.historical_otd_target AS carrier_target_otd,
    
    -- Merchant Dimension
    m.merchant_id,
    m.merchant_name,
    m.merchant_tier,
    m.industry_category,
    
    -- Geography Dimensions
    g_orig.state_region AS origin_region,
    g_orig.zone_type AS origin_zone_type,
    g_dest.state_region AS destination_region,
    g_dest.zone_type AS destination_zone_type,
    g_dest.remote_surcharge AS destination_remote_surcharge,
    
    -- Date Dimension Attributes
    d.year AS order_year,
    d.quarter AS order_quarter,
    d.month AS order_month,
    d.month_name AS order_month_name,
    d.week_of_year AS order_week_of_year,
    d.day_name AS order_day_name,
    d.is_weekend AS order_is_weekend

FROM fact_shipments s
LEFT JOIN dim_carriers c ON s.carrier_id = c.carrier_id
LEFT JOIN dim_merchants m ON s.merchant_id = m.merchant_id
LEFT JOIN dim_geography g_orig ON s.origin_geo_id = g_orig.geo_id
LEFT JOIN dim_geography g_dest ON s.dest_geo_id = g_dest.geo_id
LEFT JOIN dim_date d ON s.order_date_id = d.date_id;


-- 2. LOOKER STUDIO AGGREGATED EXECUTIVE DASHBOARD FEED
CREATE OR REPLACE VIEW v_looker_executive_kpis AS
SELECT 
    d.year,
    d.month,
    d.month_name,
    c.carrier_name,
    c.contract_tier,
    m.industry_category,
    g_dest.state_region AS destination_region,
    
    COUNT(s.shipment_id) AS total_shipments,
    SUM(s.gross_revenue) AS total_gmv,
    SUM(s.billed_carrier_cost) AS total_carrier_cost,
    SUM(s.net_margin) AS total_net_margin,
    ROUND((SUM(s.net_margin) / NULLIF(SUM(s.gross_revenue), 0)) * 100, 2) AS net_margin_ratio_pct,
    
    SUM(CASE WHEN s.is_sla_breached = 0 THEN 1 ELSE 0 END) AS on_time_shipments_count,
    SUM(s.is_sla_breached) AS sla_breached_count,
    ROUND((1.0 - (SUM(s.is_sla_breached) * 1.0 / COUNT(s.shipment_id))) * 100, 2) AS otd_rate_pct,
    
    ROUND(AVG(s.transit_time_days), 2) AS avg_transit_days,
    SUM(s.carrier_cost_variance) AS total_carrier_cost_variance,
    SUM(s.is_weight_discrepancy) AS total_weight_discrepancies

FROM fact_shipments s
JOIN dim_carriers c ON s.carrier_id = c.carrier_id
JOIN dim_merchants m ON s.merchant_id = m.merchant_id
JOIN dim_geography g_dest ON s.dest_geo_id = g_dest.geo_id
JOIN dim_date d ON s.order_date_id = d.date_id
GROUP BY 
    d.year,
    d.month,
    d.month_name,
    c.carrier_name,
    c.contract_tier,
    m.industry_category,
    g_dest.state_region;
