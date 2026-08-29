"""
GP-007: Logistics & Shipping Executive Analytics Hub (Skydropx / Frenet)
Module: Kimball Star Schema & OLAP Dimensional Engine (dimensional_model.py)

Transforms raw logistics events into an optimized Kimball Star Schema using DuckDB,
enforcing strict foreign key constraints, calculating pre-aggregated analytical views,
and exporting to compressed Parquet & DuckDB OLAP stores for Power BI, Tableau, and Excel.
"""

import os
import time
import argparse
from typing import Dict, Any
import duckdb
import pandas as pd


class DimensionalModelEngine:
    """
    High-performance DuckDB analytical transformation engine.
    Constructs the Kimball Star Schema and analytical aggregate views.
    """

    def __init__(self, raw_data_dir: str = "data/raw", processed_data_dir: str = "data/processed"):
        self.raw_data_dir = raw_data_dir
        self.processed_data_dir = processed_data_dir
        os.makedirs(self.processed_data_dir, exist_ok=True)
        self.db_path = os.path.join(self.processed_data_dir, "logistics_analytics.duckdb")
        self.conn = duckdb.connect(self.db_path)

    def initialize_schema(self):
        """Creates or replaces the star schema views and tables in DuckDB."""
        print("[Dimensional Engine] Initializing Kimball Star Schema in DuckDB...")

        # 1. Mount Raw Parquet Sources into DuckDB Virtual Tables
        self.conn.execute(f"""
            CREATE OR REPLACE VIEW v_raw_date AS 
            SELECT * FROM read_parquet('{os.path.join(self.raw_data_dir, "dim_date.parquet")}');
            
            CREATE OR REPLACE VIEW v_raw_carriers AS 
            SELECT * FROM read_parquet('{os.path.join(self.raw_data_dir, "dim_carriers.parquet")}');
            
            CREATE OR REPLACE VIEW v_raw_geography AS 
            SELECT * FROM read_parquet('{os.path.join(self.raw_data_dir, "dim_geography.parquet")}');
            
            CREATE OR REPLACE VIEW v_raw_merchants AS 
            SELECT * FROM read_parquet('{os.path.join(self.raw_data_dir, "dim_merchants.parquet")}');
            
            CREATE OR REPLACE VIEW v_raw_quotes AS 
            SELECT * FROM read_parquet('{os.path.join(self.raw_data_dir, "fact_carrier_quotes.parquet")}');
            
            CREATE OR REPLACE VIEW v_raw_shipments AS 
            SELECT * FROM read_parquet('{os.path.join(self.raw_data_dir, "fact_shipments.parquet")}');
        """)

        # 2. Build Clean Dimension Tables
        self.conn.execute("""
            CREATE OR REPLACE TABLE dim_date AS
            SELECT 
                date_id,
                full_date,
                year,
                quarter,
                month,
                month_name,
                week_of_year,
                day_of_month,
                day_of_week,
                day_name,
                is_weekend,
                is_month_end
            FROM v_raw_date;

            CREATE OR REPLACE TABLE dim_carriers AS
            SELECT 
                carrier_id,
                carrier_name,
                carrier_code,
                contract_tier,
                service_level,
                base_sla_days,
                base_rate_per_kg,
                historical_otd_target,
                weight_audit_freq
            FROM v_raw_carriers;

            CREATE OR REPLACE TABLE dim_geography AS
            SELECT 
                geo_id,
                zone_code,
                state_region,
                zone_type,
                remote_surcharge
            FROM v_raw_geography;

            CREATE OR REPLACE TABLE dim_merchants AS
            SELECT 
                merchant_id,
                merchant_name,
                tier AS merchant_tier,
                category AS industry_category,
                margin_markup_pct
            FROM v_raw_merchants;
        """)

        # 3. Build Fact Tables with Foreign Key Integrity & Calculated Measures
        self.conn.execute("""
            CREATE OR REPLACE TABLE fact_carrier_quotes AS
            SELECT 
                q.quote_id,
                q.merchant_id,
                q.carrier_id,
                q.origin_geo_id,
                q.dest_geo_id,
                q.quote_date_id,
                CAST(q.quote_timestamp AS TIMESTAMP) AS quote_timestamp,
                q.declared_weight_kg,
                q.quoted_rate,
                q.estimated_transit_days,
                q.was_converted_to_shipment
            FROM v_raw_quotes q;

            CREATE OR REPLACE TABLE fact_shipments AS
            SELECT 
                s.shipment_id,
                s.quote_id,
                s.tracking_number,
                s.merchant_id,
                s.carrier_id,
                s.origin_geo_id,
                s.dest_geo_id,
                s.order_date_id,
                CAST(s.order_timestamp AS TIMESTAMP) AS order_timestamp,
                s.promised_delivery_date_id,
                s.actual_delivery_date_id,
                CAST(s.actual_delivery_timestamp AS TIMESTAMP) AS actual_delivery_timestamp,
                s.service_level,
                s.delivery_status,
                s.declared_weight_kg,
                s.billed_weight_kg,
                s.is_weight_discrepancy,
                s.quoted_shipping_fee,
                s.billed_carrier_cost,
                s.carrier_cost_variance,
                s.gross_revenue,
                s.net_margin,
                ROUND((s.net_margin / NULLIF(s.gross_revenue, 0)) * 100, 2) AS net_margin_pct,
                s.transit_time_days,
                s.promised_sla_days,
                s.is_sla_breached,
                s.is_exception
            FROM v_raw_shipments s;
        """)

        # 4. Build Analytical Summary Views for High-Speed Reporting
        self.conn.execute("""
            -- Carrier Scorecard Summary
            CREATE OR REPLACE VIEW v_carrier_performance_scorecard AS
            SELECT 
                c.carrier_id,
                c.carrier_name,
                c.service_level,
                c.contract_tier,
                COUNT(s.shipment_id) AS total_shipments,
                ROUND(AVG(s.transit_time_days), 2) AS avg_transit_days,
                ROUND(AVG(s.promised_sla_days), 2) AS avg_promised_sla_days,
                SUM(s.is_sla_breached) AS total_sla_breaches,
                ROUND((1.0 - (SUM(s.is_sla_breached) * 1.0 / COUNT(s.shipment_id))) * 100, 2) AS otd_rate_pct,
                SUM(s.is_weight_discrepancy) AS total_weight_discrepancies,
                ROUND(SUM(s.gross_revenue), 2) AS total_gross_revenue,
                ROUND(SUM(s.billed_carrier_cost), 2) AS total_carrier_cost,
                ROUND(SUM(s.net_margin), 2) AS total_net_margin,
                ROUND(AVG(s.net_margin_pct), 2) AS avg_margin_pct,
                ROUND(SUM(s.carrier_cost_variance), 2) AS total_cost_leakage
            FROM fact_shipments s
            JOIN dim_carriers c ON s.carrier_id = c.carrier_id
            GROUP BY c.carrier_id, c.carrier_name, c.service_level, c.contract_tier
            ORDER BY total_shipments DESC;

            -- Monthly Executive KPI Trend
            CREATE OR REPLACE VIEW v_monthly_executive_trend AS
            SELECT 
                d.year,
                d.month,
                d.month_name,
                COUNT(s.shipment_id) AS total_shipments,
                ROUND(SUM(s.gross_revenue), 2) AS gross_revenue,
                ROUND(SUM(s.net_margin), 2) AS net_margin,
                ROUND((SUM(s.net_margin) / SUM(s.gross_revenue)) * 100, 2) AS margin_ratio_pct,
                ROUND((1.0 - (SUM(s.is_sla_breached) * 1.0 / COUNT(s.shipment_id))) * 100, 2) AS otd_rate_pct,
                ROUND(AVG(s.transit_time_days), 2) AS avg_transit_time_days,
                SUM(s.is_exception) AS exception_count
            FROM fact_shipments s
            JOIN dim_date d ON s.order_date_id = d.date_id
            GROUP BY d.year, d.month, d.month_name
            ORDER BY d.year, d.month;

            -- Regional Route Matrix & SLA Performance
            CREATE OR REPLACE VIEW v_regional_sla_matrix AS
            SELECT 
                g_dest.state_region AS destination_region,
                g_dest.zone_type,
                COUNT(s.shipment_id) AS shipment_volume,
                ROUND(AVG(s.transit_time_days), 2) AS avg_transit_days,
                ROUND((1.0 - (SUM(s.is_sla_breached) * 1.0 / COUNT(s.shipment_id))) * 100, 2) AS otd_pct,
                ROUND(SUM(s.gross_revenue), 2) AS regional_gmv,
                ROUND(SUM(s.net_margin), 2) AS regional_net_margin
            FROM fact_shipments s
            JOIN dim_geography g_dest ON s.dest_geo_id = g_dest.geo_id
            GROUP BY g_dest.state_region, g_dest.zone_type
            ORDER BY shipment_volume DESC;
        """)

        print("[Dimensional Engine] Schema initialization complete.")

    def export_processed_parquet(self):
        """Exports the processed Kimball tables to parquet for BI tools."""
        tables = ["dim_date", "dim_carriers", "dim_geography", "dim_merchants", "fact_carrier_quotes", "fact_shipments"]
        for table in tables:
            out_file = os.path.join(self.processed_data_dir, f"{table}.parquet")
            self.conn.execute(f"COPY {table} TO '{out_file}' (FORMAT PARQUET, COMPRESSION ZSTD);")
            count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"[Dimensional Engine] Processed '{table}' exported: {count:,} rows -> {out_file}")

    def get_carrier_scorecard(self) -> pd.DataFrame:
        """Returns the carrier scorecard as a pandas DataFrame."""
        return self.conn.execute("SELECT * FROM v_carrier_performance_scorecard").df()

    def get_monthly_trend(self) -> pd.DataFrame:
        """Returns the monthly executive trend as a pandas DataFrame."""
        return self.conn.execute("SELECT * FROM v_monthly_executive_trend").df()

    def get_regional_matrix(self) -> pd.DataFrame:
        """Returns the regional SLA matrix as a pandas DataFrame."""
        return self.conn.execute("SELECT * FROM v_regional_sla_matrix").df()

    def get_merchant_performance(self) -> pd.DataFrame:
        """Returns merchant volume and margin ranking."""
        query = """
            SELECT 
                m.merchant_id,
                m.merchant_name,
                m.merchant_tier,
                m.industry_category,
                COUNT(s.shipment_id) AS total_shipments,
                ROUND(SUM(s.gross_revenue), 2) AS total_gross_revenue,
                ROUND(SUM(s.net_margin), 2) AS total_net_margin,
                ROUND((SUM(s.net_margin) / NULLIF(SUM(s.gross_revenue), 0)) * 100, 2) AS margin_pct,
                SUM(s.is_weight_discrepancy) AS audited_discrepancies
            FROM fact_shipments s
            JOIN dim_merchants m ON s.merchant_id = m.merchant_id
            GROUP BY m.merchant_id, m.merchant_name, m.merchant_tier, m.industry_category
            ORDER BY total_gross_revenue DESC
        """
        return self.conn.execute(query).df()


def main():
    print("=" * 80)
    print(">> GP-007: DUCKDB KIMBALL STAR SCHEMA & DIMENSIONAL ENGINE")
    print("=" * 80)
    start_time = time.time()
    
    engine = DimensionalModelEngine()
    engine.initialize_schema()
    engine.export_processed_parquet()

    elapsed = (time.time() - start_time) * 1000
    print(f">> [Dimensional Engine] Pipeline executed successfully in {elapsed:.2f} ms")


if __name__ == "__main__":
    main()
