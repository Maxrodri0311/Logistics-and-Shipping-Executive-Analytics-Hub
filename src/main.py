"""
Logistics KPI Automation & Multi-Carrier Analytics Platform
Module: Master Pipeline Orchestrator (main.py)

Executes the end-to-end automated analytics lifecycle:
1. Synthetic High-Density Logistics Ingestion (data_generator.py)
2. DuckDB Kimball Star Schema & OLAP Modeling (dimensional_model.py)
3. C-Level Executive Excel KPI Dashboard Compilation (excel_builder.py)
4. Telemetry and Business Outcome Summarization
"""

import os
import sys
import time
import argparse

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_generator import LogisticsDataGenerator
from src.dimensional_model import DimensionalModelEngine
from src.excel_builder import ExecutiveExcelBuilder


def run_full_pipeline(shipments: int = 35000, quotes: int = 50000, days: int = 180):
    total_start = time.time()
    print("=" * 85)
    print(">> END-TO-END EXECUTIVE LOGISTICS ANALYTICS PIPELINE")
    print(f">> Target Volume: {shipments:,} shipments | {quotes:,} quotes | {days} days history")
    print("=" * 85)

    # Step 1: Data Generation
    t0 = time.time()
    print("\n[Step 1/3] Generating High-Density Synthetic Logistics Lakehouse...")
    generator = LogisticsDataGenerator(seed=42)
    tables = generator.generate_dataset(num_shipments=shipments, num_quotes=quotes, days_history=days)
    generator.export_to_parquet(tables, output_dir="data/raw")
    print(f">> Step 1 finished in {(time.time() - t0):.2f}s")

    # Step 2: Kimball Star Schema OLAP Processing
    t1 = time.time()
    print("\n[Step 2/3] Initializing DuckDB Kimball Star Schema & OLAP Aggregations...")
    engine = DimensionalModelEngine()
    engine.initialize_schema()
    engine.export_processed_parquet()
    print(f">> Step 2 finished in {(time.time() - t1):.2f}s")

    # Step 3: Executive Excel Dashboard Compilation
    t2 = time.time()
    print("\n[Step 3/3] Compiling C-Level Executive Excel KPI Dashboard (.xlsx)...")
    builder = ExecutiveExcelBuilder(output_path="dist/Executive_Logistics_KPI_Dashboard.xlsx")
    builder.generate_workbook()
    print(f">> Step 3 finished in {(time.time() - t2):.2f}s")

    # Summary Report
    total_time = (time.time() - total_start)
    scorecard = engine.get_carrier_scorecard()
    
    print("\n" + "=" * 85)
    print(f">> PIPELINE COMPLETED SUCCESSFULLY IN {total_time:.2f} SECONDS")
    print("=" * 85)
    print("[EXECUTIVE CARRIER SCORECARD PREVIEW]")
    print("-" * 85)
    print(scorecard[["carrier_name", "total_shipments", "otd_rate_pct", "total_gross_revenue", "total_net_margin", "total_cost_leakage"]].to_string(index=False))
    print("=" * 85)
    print("[Master Deliverables Generated]")
    print("   * DuckDB Database:        data/processed/logistics_analytics.duckdb")
    print("   * Processed Parquet OLAP: data/processed/*.parquet")
    print("   * Executive Dashboard:    dist/Executive_Logistics_KPI_Dashboard.xlsx")
    print("   * DAX Semantic Layer:     src/dax_measures.dax")
    print("   * Tableau/Looker Views:   src/tableau_looker_views.sql")
    print("=" * 85)



def main():
    parser = argparse.ArgumentParser(description="Logistics Master Analytics Pipeline")
    parser.add_argument("--shipments", type=int, default=35000, help="Shipment volume")
    parser.add_argument("--quotes", type=int, default=50000, help="Quotes volume")
    parser.add_argument("--days", type=int, default=180, help="Historical days range")
    args = parser.parse_args()

    run_full_pipeline(shipments=args.shipments, quotes=args.quotes, days=args.days)


if __name__ == "__main__":
    main()