"""
GP-007: Logistics & Shipping Executive Analytics Hub (Skydropx / Frenet)
Module: Quantitative Performance & Compression Benchmark (run_benchmark.py)

Measures DuckDB OLAP query latencies (p50, p95, p99), memory efficiency, and
columnar compression ratios on high-volume logistics datasets (50k+ shipments).
"""

import os
import sys
import time
import numpy as np
import pandas as pd

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_generator import LogisticsDataGenerator
from src.dimensional_model import DimensionalModelEngine


def benchmark_query_latency(engine: DimensionalModelEngine, query: str, iterations: int = 50) -> dict:
    """Executes a query multiple times and computes latency percentiles in ms."""
    latencies = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        engine.conn.execute(query).fetchall()
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

    return {
        "p50_ms": float(np.percentile(latencies, 50)),
        "p95_ms": float(np.percentile(latencies, 95)),
        "p99_ms": float(np.percentile(latencies, 99)),
        "avg_ms": float(np.mean(latencies)),
        "min_ms": float(np.min(latencies)),
        "max_ms": float(np.max(latencies)),
    }


def compute_compression_metrics(raw_dir: str = "data/raw", proc_dir: str = "data/processed") -> dict:
    """Calculates dataset compression metrics comparing uncompressed vs parquet vs duckdb."""
    raw_shipments_path = os.path.join(raw_dir, "fact_shipments.parquet")
    proc_shipments_path = os.path.join(proc_dir, "fact_shipments.parquet")
    duckdb_path = os.path.join(proc_dir, "logistics_analytics.duckdb")

    if not os.path.exists(proc_shipments_path):
        return {}

    df = pd.read_parquet(proc_shipments_path)
    # Estimate uncompressed in-memory CSV size
    uncompressed_bytes = df.memory_usage(deep=True).sum()
    parquet_bytes = os.path.getsize(proc_shipments_path)
    duckdb_bytes = os.path.getsize(duckdb_path) if os.path.exists(duckdb_path) else 0

    compression_ratio_parquet = (1.0 - (parquet_bytes / uncompressed_bytes)) * 100.0
    compression_ratio_duckdb = (1.0 - (duckdb_bytes / uncompressed_bytes)) * 100.0 if duckdb_bytes else 0.0

    return {
        "row_count": len(df),
        "uncompressed_mb": uncompressed_bytes / (1024 * 1024),
        "parquet_mb": parquet_bytes / (1024 * 1024),
        "duckdb_mb": duckdb_bytes / (1024 * 1024),
        "parquet_compression_pct": compression_ratio_parquet,
        "duckdb_compression_pct": compression_ratio_duckdb,
    }


def main():
    print("=" * 85)
    print(">> GP-007: QUANTITATIVE BENCHMARKING SUITE (DUCKDB & KIMBALL STAR SCHEMA)")
    print("=" * 85)

    # Ingest / Benchmark on current processed lakehouse
    engine = DimensionalModelEngine()

    queries = {
        "Q1: Carrier Scorecard Aggregation": """
            SELECT 
                c.carrier_name,
                COUNT(s.shipment_id) AS total_shipments,
                ROUND(AVG(s.transit_time_days), 2) AS avg_transit,
                ROUND((1.0 - (SUM(s.is_sla_breached) * 1.0 / COUNT(s.shipment_id))) * 100, 2) AS otd_pct,
                ROUND(SUM(s.gross_revenue), 2) AS total_gmv,
                ROUND(SUM(s.net_margin), 2) AS net_margin
            FROM fact_shipments s
            JOIN dim_carriers c ON s.carrier_id = c.carrier_id
            GROUP BY c.carrier_name;
        """,
        "Q2: Time Intelligence Monthly & Merchant Trend": """
            SELECT 
                d.year, d.month, m.merchant_tier,
                COUNT(s.shipment_id) AS shipments,
                SUM(s.gross_revenue) AS gmv,
                SUM(s.carrier_cost_variance) AS total_leakage
            FROM fact_shipments s
            JOIN dim_date d ON s.order_date_id = d.date_id
            JOIN dim_merchants m ON s.merchant_id = m.merchant_id
            GROUP BY d.year, d.month, m.merchant_tier;
        """,
        "Q3: Regional Route & SLA Matrix Slice": """
            SELECT 
                g.state_region, g.zone_type,
                COUNT(s.shipment_id) AS vol,
                ROUND(AVG(s.transit_time_days), 2) AS avg_transit,
                ROUND(SUM(s.net_margin), 2) AS regional_margin
            FROM fact_shipments s
            JOIN dim_geography g ON s.dest_geo_id = g.geo_id
            GROUP BY g.state_region, g.zone_type;
        """
    }

    print("\n[1/2] Benchmarking Analytical Query Latency (50 iterations per query)...")
    print("-" * 85)
    print(f"{'Query Description':<45} | {'p50 (ms)':<9} | {'p95 (ms)':<9} | {'p99 (ms)':<9} | {'Avg (ms)':<9}")
    print("-" * 85)

    benchmark_results = {}
    for q_name, sql in queries.items():
        res = benchmark_query_latency(engine, sql, iterations=50)
        benchmark_results[q_name] = res
        print(f"{q_name:<45} | {res['p50_ms']:>9.2f} | {res['p95_ms']:>9.2f} | {res['p99_ms']:>9.2f} | {res['avg_ms']:>9.2f}")

    print("-" * 85)

    print("\n[2/2] Storage & Memory Compression Efficiency...")
    print("-" * 85)
    comp = compute_compression_metrics()
    if comp:
        print(f"  * Total Analytical Fact Records: {comp['row_count']:,} rows")
        print(f"  * In-Memory Uncompressed Size:    {comp['uncompressed_mb']:.2f} MB")
        print(f"  * Parquet (Snappy/ZSTD) Size:     {comp['parquet_mb']:.2f} MB ({comp['parquet_compression_pct']:.1f}% space saved)")
        print(f"  * Native DuckDB OLAP DB Size:     {comp['duckdb_mb']:.2f} MB")
    print("=" * 85)
    print(">> Benchmark completed successfully.")


if __name__ == "__main__":
    main()
