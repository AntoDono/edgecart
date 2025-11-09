"""
Knot API to Snowflake Ingestion Pipeline
Pulls customer purchase data from Knot API and stores in Snowflake
"""

from typing import List, Dict
from datetime import datetime, timedelta
import json
from snowflake_connector import get_snowflake_connector


class KnotDataIngestion:
    """
    Handles ingestion of Knot API data into Snowflake warehouse
    """

    def __init__(self):
        self.sf = get_snowflake_connector()
        self.table_name = "CUSTOMER_TRANSACTIONS"
        self.schema = "RAW_DATA"

    def setup_tables(self):
        """Create necessary tables in Snowflake"""
        print("🏗️  Setting up Snowflake tables for Knot data...")

        # Customer Transactions table
        transactions_schema = {
            "transaction_id": "VARCHAR(255)",
            "customer_id": "VARCHAR(255)",
            "merchant_id": "VARCHAR(255)",
            "amount": "DECIMAL(10,2)",
            "transaction_date": "TIMESTAMP",
            "items": "VARIANT",
            "metadata": "VARIANT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP()"
        }

        self.sf.create_table_if_not_exists(self.table_name, transactions_schema)

        # Purchase History table
        history_schema = {
            "purchase_id": "VARCHAR(255)",
            "customer_id": "VARCHAR(255)",
            "product_name": "VARCHAR(500)",
            "category": "VARCHAR(100)",
            "quantity": "INTEGER",
            "unit_price": "DECIMAL(10,2)",
            "purchase_date": "TIMESTAMP",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP()"
        }

        self.sf.create_table_if_not_exists("PURCHASE_HISTORY", history_schema)

        print("✅ Snowflake tables ready")

    def fetch_knot_transactions(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Fetch transactions from Knot API
        """
        print(f"🔄 Fetching Knot transactions from {start_date} to {end_date}...")

        # Simulated API call
        transactions = []

        print(f"✅ Retrieved {len(transactions)} transactions from Knot API")
        return transactions

    def transform_transaction_data(self, raw_transactions: List[Dict]) -> List[Dict]:
        """
        Transform Knot API data for Snowflake schema
        """
        print(f"🔧 Transforming {len(raw_transactions)} transactions...")

        transformed = []
        for tx in raw_transactions:
            transformed.append({
                "transaction_id": tx.get("id"),
                "customer_id": tx.get("user_id"),
                "merchant_id": tx.get("merchant_id"),
                "amount": tx.get("amount"),
                "transaction_date": tx.get("date"),
                "items": json.dumps(tx.get("items", [])),
                "metadata": json.dumps(tx.get("metadata", {}))
            })

        print(f"✅ Transformed {len(transformed)} records")
        return transformed

    def ingest_to_snowflake(self, transactions: List[Dict]) -> bool:
        """
        Insert transformed transactions into Snowflake
        """
        if not transactions:
            print("⚠️  No transactions to ingest")
            return False

        print(f"📊 Ingesting {len(transactions)} transactions to Snowflake...")

        # Connect to Snowflake
        self.sf.connect()

        # Batch insert
        success = self.sf.insert_batch(self.table_name, transactions)

        # Close connection
        self.sf.close()

        return success

    def run_ingestion(self, days_back: int = 7):
        """
        Run full ingestion pipeline
        """
        print("🚀 Starting Knot → Snowflake ingestion pipeline...")
        print(f"   Ingesting last {days_back} days of data")

        # Setup tables
        self.setup_tables()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Fetch from Knot API
        raw_transactions = self.fetch_knot_transactions(start_date, end_date)

        # Transform data
        transformed_transactions = self.transform_transaction_data(raw_transactions)

        # Ingest to Snowflake
        success = self.ingest_to_snowflake(transformed_transactions)

        if success:
            print("✅ Knot ingestion pipeline completed successfully")
        else:
            print("❌ Knot ingestion pipeline failed")

        return success


if __name__ == "__main__":
    # Run ingestion pipeline
    ingestion = KnotDataIngestion()
    ingestion.run_ingestion(days_back=30)
