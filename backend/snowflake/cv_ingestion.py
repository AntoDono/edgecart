"""
Computer Vision to Snowflake Ingestion Pipeline
Stores freshness detection results in Snowflake warehouse
"""

from typing import List, Dict
from datetime import datetime
import json
from snowflake_connector import get_snowflake_connector


class CVDataIngestion:
    """
    Handles ingestion of computer vision freshness data into Snowflake
    """

    def __init__(self):
        self.sf = get_snowflake_connector()
        self.sf.schema = "INVENTORY_DATA"

    def setup_tables(self):
        """Create CV data tables in Snowflake"""
        print("🏗️  Setting up Snowflake tables for CV data...")

        # Freshness Scores table
        freshness_schema = {
            "detection_id": "VARCHAR(255) PRIMARY KEY",
            "camera_id": "VARCHAR(100)",
            "product_id": "VARCHAR(255)",
            "fruit_type": "VARCHAR(100)",
            "freshness_score": "DECIMAL(5,2)",
            "confidence": "DECIMAL(5,2)",
            "blemish_count": "INTEGER",
            "shelf_life_days": "INTEGER",
            "image_path": "VARCHAR(500)",
            "bounding_box": "VARIANT",
            "detection_timestamp": "TIMESTAMP",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP()"
        }

        self.sf.create_table_if_not_exists("FRESHNESS_SCORES", freshness_schema)

        # Inventory Snapshots table
        snapshot_schema = {
            "snapshot_id": "VARCHAR(255) PRIMARY KEY",
            "store_id": "VARCHAR(100)",
            "section": "VARCHAR(100)",
            "total_items": "INTEGER",
            "avg_freshness": "DECIMAL(5,2)",
            "items_below_threshold": "INTEGER",
            "snapshot_timestamp": "TIMESTAMP",
            "metadata": "VARIANT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP()"
        }

        self.sf.create_table_if_not_exists("INVENTORY_SNAPSHOTS", snapshot_schema)

        print("✅ CV data tables ready")

    def process_freshness_detection(self, detection_result: Dict) -> Dict:
        """
        Transform CV detection result for Snowflake
        """
        return {
            "detection_id": detection_result.get("id"),
            "camera_id": detection_result.get("camera_id"),
            "product_id": detection_result.get("product_id"),
            "fruit_type": detection_result.get("fruit_type"),
            "freshness_score": detection_result.get("freshness_score"),
            "confidence": detection_result.get("confidence"),
            "blemish_count": detection_result.get("blemish_count", 0),
            "shelf_life_days": detection_result.get("estimated_shelf_life"),
            "image_path": detection_result.get("image_path"),
            "bounding_box": json.dumps(detection_result.get("bbox", {})),
            "detection_timestamp": datetime.now().isoformat()
        }

    def ingest_cv_data(self, detections: List[Dict]) -> bool:
        """
        Insert CV detection results into Snowflake
        """
        if not detections:
            print("⚠️  No CV detections to ingest")
            return False

        print(f"📊 Ingesting {len(detections)} CV detections to Snowflake...")

        # Transform detections
        transformed = [self.process_freshness_detection(d) for d in detections]

        # Connect to Snowflake
        self.sf.connect()

        # Batch insert
        success = self.sf.insert_batch("FRESHNESS_SCORES", transformed)

        # Close connection
        self.sf.close()

        return success

    def create_inventory_snapshot(self, store_id: str, section: str) -> bool:
        """
        Create aggregated inventory snapshot
        """
        print(f"📸 Creating inventory snapshot for {store_id}/{section}...")

        # Query recent freshness scores
        query = f"""
            SELECT
                COUNT(*) as total_items,
                AVG(freshness_score) as avg_freshness,
                SUM(CASE WHEN freshness_score < 50 THEN 1 ELSE 0 END) as items_below_threshold
            FROM INVENTORY_DATA.FRESHNESS_SCORES
            WHERE camera_id LIKE '{store_id}%'
            AND detection_timestamp >= DATEADD(hour, -1, CURRENT_TIMESTAMP())
        """

        # Execute query
        self.sf.connect()
        results = self.sf.execute_query(query)
        self.sf.close()

        if results:
            snapshot = {
                "snapshot_id": f"{store_id}_{section}_{datetime.now().timestamp()}",
                "store_id": store_id,
                "section": section,
                "total_items": results[0].get("total_items", 0),
                "avg_freshness": results[0].get("avg_freshness", 0),
                "items_below_threshold": results[0].get("items_below_threshold", 0),
                "snapshot_timestamp": datetime.now().isoformat(),
                "metadata": json.dumps({"source": "cv_pipeline"})
            }

            # Insert snapshot
            self.sf.connect()
            success = self.sf.insert_batch("INVENTORY_SNAPSHOTS", [snapshot])
            self.sf.close()

            return success

        return False

    def run_ingestion(self, detections: List[Dict], store_id: str = "store_001"):
        """
        Run full CV ingestion pipeline
        """
        print("🚀 Starting CV → Snowflake ingestion pipeline...")

        # Setup tables
        self.setup_tables()

        # Ingest detections
        success = self.ingest_cv_data(detections)

        # Create snapshot
        if success:
            self.create_inventory_snapshot(store_id, "produce")

        if success:
            print("✅ CV ingestion pipeline completed successfully")
        else:
            print("❌ CV ingestion pipeline failed")

        return success


if __name__ == "__main__":
    # Example CV detection results
    example_detections = [
        {
            "id": "det_001",
            "camera_id": "cam_produce_01",
            "product_id": "prod_banana_001",
            "fruit_type": "banana",
            "freshness_score": 85.5,
            "confidence": 0.95,
            "blemish_count": 2,
            "estimated_shelf_life": 4,
            "image_path": "/images/banana_001.jpg",
            "bbox": {"x": 100, "y": 150, "width": 200, "height": 250}
        }
    ]

    # Run ingestion
    ingestion = CVDataIngestion()
    ingestion.run_ingestion(example_detections)
