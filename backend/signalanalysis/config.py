"""
Grok Signal Analysis Configuration
API keys and settings for real-time waste detection
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Grok API Configuration
XAI_API_KEY = os.getenv('XAI_API_KEY')
XAI_API_BASE = 'https://api.x.ai/v1'
GROK_MODEL = 'grok-3-mini'  # Reasoning model for signal analysis

# Snowflake Connection (reuse from main config)
from backend.snowflake.config import DB_CONFIG

# Monitoring Settings
MONITORING_INTERVAL = 300  # 5 minutes in seconds
LOOKBACK_HOURS = 24  # How far back to analyze trends
ALERT_THRESHOLD_URGENT = 0.85  # 85% confidence for urgent alerts
ALERT_THRESHOLD_WARNING = 0.65  # 65% confidence for warnings

# Signal Detection Thresholds
DECAY_ACCELERATION_THRESHOLD = 2.0  # 2x faster than normal
PURCHASE_DROP_THRESHOLD = 0.40  # 40% decrease
INVENTORY_WASTE_THRESHOLD = 100  # $100 potential loss
FRESHNESS_CRITICAL = 50  # Score below 50 is critical

# Weather API (for correlation analysis)
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5'

# Notification Settings
ENABLE_ALERTS = True
ALERT_EMAIL = 'alerts@edgecart.com'
ALERT_SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK')

# Performance Tracking
LOG_PREDICTIONS = True
PREDICTION_LOG_PATH = './logs/signal_predictions.jsonl'

if XAI_API_KEY:
    print("✅ Grok signal analysis configuration loaded")
    print(f"   Model: {GROK_MODEL}")
    print(f"   Monitoring interval: {MONITORING_INTERVAL}s")
    print(f"   Lookback window: {LOOKBACK_HOURS}h")
else:
    print("⚠️  Grok configuration loaded (missing API key - set XAI_API_KEY in .env)")
