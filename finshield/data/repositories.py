from typing import List, Optional
from finshield.database.connection import get_duckdb_connection
from finshield.models.domain import Customer, CustomerProfile, Transaction, TransactionProfile, FinancialCase
from finshield.exceptions import CustomerNotFoundError

class CustomerRepository:
    @staticmethod
    def get_customer(customer_id: str) -> Customer:
        with get_duckdb_connection() as con:
            result = con.execute(
                "SELECT * FROM finshield_customers WHERE finshield_customer_id = ?",
                [customer_id]
            ).fetchone()
            
            if not result:
                raise CustomerNotFoundError(customer_id)
                
            cols = [desc[0] for desc in con.description]
            return Customer(**dict(zip(cols, result)))

    @staticmethod
    def get_customer_profile(customer_id: str) -> Optional[CustomerProfile]:
        with get_duckdb_connection() as con:
            result = con.execute(
                "SELECT * FROM finshield_customer_profiles WHERE finshield_customer_id = ?",
                [customer_id]
            ).fetchone()
            
            if not result:
                return None
                
            cols = [desc[0] for desc in con.description]
            return CustomerProfile(**dict(zip(cols, result)))


class TransactionRepository:
    @staticmethod
    def get_transaction_profile(account_id: str) -> Optional[TransactionProfile]:
        with get_duckdb_connection() as con:
            result = con.execute(
                "SELECT * FROM transaction_profiles WHERE account_id = ?",
                [account_id]
            ).fetchone()
            
            if not result:
                return None
                
            cols = [desc[0] for desc in con.description]
            return TransactionProfile(**dict(zip(cols, result)))

    @staticmethod
    def get_recent_transactions(account_id: str, limit: int = 50) -> List[Transaction]:
        """
        Uses aggregation and filtering to avoid loading massive histories.
        """
        with get_duckdb_connection() as con:
            results = con.execute(
                "SELECT * FROM transactions WHERE name_orig = ? ORDER BY step DESC LIMIT ?",
                [account_id, limit]
            ).fetchall()
            
            cols = [desc[0] for desc in con.description]
            return [Transaction(**dict(zip(cols, row))) for row in results]


class CaseRepository:
    @staticmethod
    def get_customer_cases(customer_id: str) -> List[FinancialCase]:
        with get_duckdb_connection() as con:
            results = con.execute(
                "SELECT * FROM financial_cases WHERE finshield_customer_id = ?",
                [customer_id]
            ).fetchall()
            
            cols = [desc[0] for desc in con.description]
            return [FinancialCase(**dict(zip(cols, row))) for row in results]
