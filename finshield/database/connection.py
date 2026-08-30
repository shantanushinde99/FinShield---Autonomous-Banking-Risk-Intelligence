import duckdb
from contextlib import contextmanager
from finshield.config.settings import settings
from finshield.exceptions import DatabaseConnectionError

@contextmanager
def get_duckdb_connection(read_only: bool = True):
    """
    Context manager for DuckDB connections.
    Always use read_only=True for investigations to prevent accidental modifications.
    """
    conn = None
    try:
        conn = duckdb.connect(settings.duckdb_path, read_only=read_only)
        yield conn
    except duckdb.Error as e:
        raise DatabaseConnectionError(f"Failed to connect to DuckDB: {str(e)}") from e
    finally:
        if conn:
            conn.close()
