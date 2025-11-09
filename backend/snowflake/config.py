"""
Snowflake Configuration
Environment variables and credentials for data pipeline
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Snowflake Credentials
SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT')
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER')
SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD')
SNOWFLAKE_WAREHOUSE = os.getenv('SNOWFLAKE_WAREHOUSE', 'EDGECART_WH')
SNOWFLAKE_DATABASE = os.getenv('SNOWFLAKE_DATABASE', 'EDGECART_DB')
SNOWFLAKE_ROLE = os.getenv('SNOWFLAKE_ROLE', 'EDGECART_ADMIN')

# Snowflake API Key (for partner connect)
SNOWFLAKE_API_KEY = os.getenv('SNOWFLAKE_API_KEY')
SNOWFLAKE_API_SECRET = os.getenv('SNOWFLAKE_API_SECRET')

# Schema Names
SCHEMA_RAW_DATA = 'RAW_DATA'
SCHEMA_INVENTORY = 'INVENTORY_DATA'
SCHEMA_ANALYTICS = 'ANALYTICS'

# Database Configuration
DB_CONFIG = {
    'account': SNOWFLAKE_ACCOUNT,
    'user': SNOWFLAKE_USER,
    'password': SNOWFLAKE_PASSWORD,
    'warehouse': SNOWFLAKE_WAREHOUSE,
    'database': SNOWFLAKE_DATABASE,
    'role': SNOWFLAKE_ROLE,
    'schema': SCHEMA_RAW_DATA
}

# Knot API Integration
KNOT_API_URL = os.getenv('KNOT_API_URL', 'https://api.knotapi.com/v1')
KNOT_CLIENT_ID = os.getenv('KNOT_CLIENT_ID')
KNOT_CLIENT_SECRET = os.getenv('KNOT_CLIENT_SECRET')

# Snowflake Streams (for real-time data)
ENABLE_STREAMS = True
STREAM_BUFFER_SIZE = 1000
STREAM_FLUSH_INTERVAL = 60  # seconds

# ML Model Settings
ML_MODEL_STORAGE = 'ANALYTICS.ML_MODELS'
MODEL_REGISTRY_PATH = '@EDGECART_DB.ANALYTICS.MODEL_REGISTRY'

# Data Retention
RAW_DATA_RETENTION_DAYS = 90
ANALYTICS_RETENTION_DAYS = 365

if SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER:
    print("✅ Snowflake configuration loaded")
    print(f"   Account: {SNOWFLAKE_ACCOUNT}")
    print(f"   User: {SNOWFLAKE_USER}")
    print(f"   Warehouse: {SNOWFLAKE_WAREHOUSE}")
else:
    print("⚠️  Snowflake configuration loaded (missing credentials - set in .env)")
