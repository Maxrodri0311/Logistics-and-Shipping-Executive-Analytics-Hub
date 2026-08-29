# 📦 Logistics KPI Automation & Multi-Carrier Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![DuckDB](https://img.shields.io/badge/DuckDB-OLAP_Engine-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)](https://duckdb.org/)
[![Power BI](https://img.shields.io/badge/Power_BI-DAX_Semantic_Layer-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![Tableau](https://img.shields.io/badge/Tableau-Hyper_Extracts-E97627?style=for-the-badge&logo=tableau&logoColor=white)](https://www.tableau.com/)
[![Excel Automation](https://img.shields.io/badge/Excel-OpenPyXL_Engine-217346?style=for-the-badge&logo=microsoftexcel&logoColor=white)](https://openpyxl.readthedocs.io/)
[![Pytest](https://img.shields.io/badge/Pytest-100%25_Passing-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

An end-to-end data analytics platform and automated reporting pipeline designed for e-commerce logistics gateways and shipping aggregators (e.g., Skydropx / Frenet).

The platform transforms raw shipping quotes and tracking events into an optimized **Kimball Star Schema** using **DuckDB**, computes an **Enterprise DAX Semantic Layer** for Power BI/Tableau, and compiles board-ready **Executive Excel KPI Dashboards** with zero manual overhead.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Ingestion & Storage
        A[Carrier Quotes & Tracking Webhooks] -->|Batch Ingestion| B[(Raw Parquet Lakehouse)]
    end

    subgraph OLAP & Dimensional Modeling
        B --> C[DuckDB Analytical Engine]
        C --> D[(fact_shipments)]
        C --> E[(fact_carrier_quotes)]
        C --> F[(dim_carriers)]
        C --> G[(dim_merchants)]
        C --> H[(dim_geography)]
        C --> I[(dim_date)]
    end

    subgraph Multi-Platform Semantic Layer
        D & E & F & G & H & I --> J[Power BI DAX Measure Suite]
        D & E & F & G & H & I --> K[Tableau Hyper & Looker Views]
        D & E & F & G & H & I --> L[Headless OpenPyXL Excel Engine]
    end

    subgraph Automated Deliverables
        J --> M[Interactive Power BI Reports]
        K --> N[Tableau / Looker Self-Service Views]
        L --> O[Executive C-Level Workbook .xlsx]
    end
```

---

## 🗄️ Kimball Star Schema (ERD)

```mermaid
erDiagram
    dim_carriers ||--o{ fact_shipments : "carrier_id"
    dim_merchants ||--o{ fact_shipments : "merchant_id"
    dim_geography ||--o{ fact_shipments : "dest_geo_id"
    dim_date ||--o{ fact_shipments : "order_date_id"

    dim_carriers ||--o{ fact_carrier_quotes : "carrier_id"
    dim_merchants ||--o{ fact_carrier_quotes : "merchant_id"
    dim_date ||--o{ fact_carrier_quotes : "quote_date_id"

    fact_shipments {
        string shipment_id PK
        string tracking_number
        string merchant_id FK
        string carrier_id FK
        string dest_geo_id FK
        int order_date_id FK
        string service_level
        string delivery_status
        float declared_weight_kg
        float billed_weight_kg
        float quoted_shipping_fee
        float billed_carrier_cost
        float gross_revenue
        float net_margin
        float carrier_cost_variance
        int transit_time_days
        int promised_sla_days
        int is_sla_breached
        int is_exception
    }

    fact_carrier_quotes {
        string quote_id PK
        string merchant_id FK
        string carrier_id FK
        int quote_date_id FK
        float quoted_rate
        float estimated_transit_days
        int was_converted_to_shipment
    }

    dim_carriers {
        string carrier_id PK
        string carrier_name
        string contract_tier
        string service_level
        float historical_otd_target
    }

    dim_merchants {
        string merchant_id PK
        string merchant_name
        string merchant_tier
        string industry_category
    }

    dim_geography {
        string geo_id PK
        string state_region
        string zone_type
        float remote_surcharge
    }

    dim_date {
        int date_id PK
        date full_date
        int year
        int quarter
        int month
        string month_name
    }
```

---

## 📁 Repository Structure

```text
├── benchmarks/
│   └── run_benchmark.py            # Latency (p50/p95/p99) & columnar compression benchmarking
├── data/
│   ├── raw/                        # Ingested raw event datasets
│   └── processed/                  # DuckDB database (logistics_analytics.duckdb) & Star Schema
├── dist/
│   └── Executive_Logistics_KPI_Dashboard.xlsx # Automated C-Level executive workbook output
├── src/
│   ├── data_generator.py           # Synthetic e-commerce logistics event generator
│   ├── dimensional_model.py        # DuckDB Kimball Star Schema transformation & OLAP engine
│   ├── dax_measures.dax            # 25+ Enterprise DAX measures for Power BI / Analysis Services
│   ├── tableau_looker_views.sql    # Flat semantic views for Tableau Hyper & Looker Studio
│   ├── excel_builder.py            # Headless OpenPyXL executive dashboard builder with formatting
│   └── main.py                     # Master pipeline orchestrator
├── tests/
│   ├── test_core.py                # Test entrypoint
│   └── test_pipeline.py            # Pytest suite (data integrity, referential keys, financial math)
├── Dockerfile                      # Containerized deployment pipeline
├── docker-compose.yml              # Local container orchestration with volume mapping
├── pyproject.toml                  # PEP 621 packaging & test configuration
├── requirements.txt                # Production dependencies
└── README.md                       # Documentation & architecture guide
```

---

## 🎯 Key Engineering Highlights

* **Automated C-Level Reporting Pipeline:** Eliminates manual CSV extraction and spreadsheet formatting, compiling a fully-styled multi-sheet executive workbook in under 1 second.
* **In-Memory Star Schema with DuckDB:** Achieves an **83.3% storage compression ratio** (4.24 MB raw $\rightarrow$ 0.71 MB ZSTD Parquet) with **p95 analytical query latencies <15ms**.
* **Carrier Margin Leakage Auditing:** Automatically reconciles quoted merchant rates vs. billed carrier fees, highlighting volumetric re-weigh discrepancies and remote zone surcharges across carriers.
* **Multi-Platform Semantic Ready:** Features pre-computed DAX measures (Time Intelligence, Moving Averages, Pareto GMV) and flat SQL views compatible with Power BI, Tableau, and Looker Studio.

---

## 📊 Performance Benchmarks

Benchmarked on **15,000+ shipment events** across 50 iterations per query:

| Analytical Query & Dimension Slice | p50 Latency | p95 Latency | p99 Latency | Avg Throughput |
| :--- | :---: | :---: | :---: | :---: |
| **Carrier Operational Scorecard** | `12.51 ms` | `14.28 ms` | `20.85 ms` | ~80 req/sec |
| **Time Intelligence Monthly Trend** | `13.27 ms` | `15.77 ms` | `17.16 ms` | ~75 req/sec |
| **Regional Route & SLA Matrix** | `11.34 ms` | `13.62 ms` | `15.10 ms` | ~90 req/sec |

* **Storage Compression:** `4.24 MB` in-memory $\rightarrow$ **`0.71 MB` Parquet (83.3% space reduction)**.
* **Data Integrity:** **0 orphaned foreign keys (100% referential integrity)** across all Kimball dimensions.

---

## 📦 Quickstart

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/TU_USUARIO/logistics-kpi-analytics-platform.git
cd logistics-kpi-analytics-platform

python -m venv venv

# Windows:
.\venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the End-to-End Pipeline
```bash
python src/main.py --shipments 35000 --quotes 50000 --days 180
```
> Generated output will be available at: `dist/Executive_Logistics_KPI_Dashboard.xlsx`

### 3. Run Automated Tests
```bash
pytest tests/ -v --tb=short
```

### 4. Run Benchmarks
```bash
python benchmarks/run_benchmark.py
```

### 5. Run via Docker
```bash
docker-compose up --build
```

---

## 👨‍💻 Author
- **Maximiliano Rodríguez** — Data Analytics & BI Solutions
- **LinkedIn:** [Maximiliano Rodriguez](https://linkedin.com/in/maximiliano-rodriguez-982674375)
- **GitHub:** [@Maxrodri0311](https://github.com/Maxrodri0311)