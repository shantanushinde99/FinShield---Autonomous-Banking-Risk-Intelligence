import argparse
import textwrap
from finshield.database.connection import get_duckdb_connection

def profile_table(con, table_name: str):
    print(f"\n{'='*60}")
    print(f"PROFILING TABLE: {table_name}")
    print(f"{'='*60}")
    
    # Row count
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"Total Rows: {count:,}")
    
    # Schema
    schema = con.execute(f"DESCRIBE {table_name}").fetchall()
    print("\nColumns:")
    for col in schema:
        col_name, col_type, null_allowed, key, default, extra = col
        print(f"  - {col_name} ({col_type})")
        
    print(f"{'-'*60}")
    print("Sample Data (First 3 Rows):")
    sample = con.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
    
    if sample:
        col_names = [col[0] for col in schema]
        for i, row in enumerate(sample):
            print(f"  Row {i+1}:")
            # Format row nicely
            row_dict = dict(zip(col_names, row))
            for k, v in list(row_dict.items())[:5]: # just show 5 cols to not clutter
                print(f"    {k}: {v}")
            if len(col_names) > 5:
                print(f"    ... and {len(col_names)-5} more columns")
    else:
        print("  (Empty Table)")
        
    print(f"{'='*60}\n")

def run_profiler():
    print("Starting Data Quality Audit...")
    try:
        with get_duckdb_connection() as con:
            tables = con.execute("SHOW TABLES").fetchall()
            
            if not tables:
                print("No tables found in DuckDB database.")
                return
                
            for table in tables:
                table_name = table[0]
                profile_table(con, table_name)
                
    except Exception as e:
        print(f"Error during profiling: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinShield Data Profiling CLI")
    args = parser.parse_args()
    
    run_profiler()
