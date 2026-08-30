# Data Architecture

## 1. Data Sources
The primary structured data source is a pre-processed DuckDB database (`finshield.duckdb`) backed by Parquet files. The data layer will abstract this into Domain Repositories to prevent arbitrary SQL execution by agents.

## 2. DuckDB Schema Assessment
Based on an inspection of the DuckDB file, the available tables and their schemas are:

### `finshield_customers`
- **Columns**: `finshield_customer_id`, `SK_ID_CURR`, `account_id`, `synthetic_dataset_mapping`
- **Purpose**: Master table linking customers to their respective dataset IDs (Home Credit vs Paysim).

### `finshield_customer_profiles`
- **Columns**: Extensive demographic and credit metrics including `finshield_customer_id`, `total_income`, `credit_amount`, `annuity`, `age`, `employment_years`, `bureau_total_outstanding_debt`, `fraud_ratio`, `credit_risk_score`, etc.
- **Purpose**: Comprehensive feature table summarizing the customer's risk profile.

### `transaction_profiles`
- **Columns**: `account_id`, `transaction_count`, `total_transaction_amount`, `fraud_ratio`, `avg_balance_change`, etc.
- **Purpose**: Aggregated transaction statistics.

### `transactions`
- **Columns**: `step`, `type`, `amount`, `name_orig`, `new_balance_orig`, `name_dest`, `new_balance_dest`, `is_fraud`, `is_flagged_fraud`
- **Purpose**: Granular transactional ledger.

### `financial_cases`
- **Columns**: `case_id`, `finshield_customer_id`, `case_text`, `credit_risk_score`, `transaction_risk_score`, `overall_risk_score`, `risk_level`
- **Purpose**: Historical investigation cases that will be embedded and ingested into Qdrant for semantic memory.

## 3. Data Abstraction Layer (Repositories)
To ensure security and predictability, the `backend/data/` layer will implement the following abstractions:
- `CustomerRepository`: Fetches `finshield_customer_profiles` by ID.
- `TransactionRepository`: Fetches granular `transactions` or aggregated `transaction_profiles`.
- `CaseRepository`: Fetches historical `financial_cases` for a given customer.

Agents will use these repositories as tools, passing explicit, typed parameters (e.g., `get_customer_profile(customer_id: str)`).
