"""
Signal Detection Logic
Analyzes Snowflake data for anomalous patterns in grocery waste
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import numpy as np


class SignalDetector:
    """
    Detects anomalous signals in grocery waste data streams
    """

    def __init__(self, snowflake_connector):
        self.sf = snowflake_connector
        self.signals_detected = []
        self.baseline_metrics = {}

    def detect_decay_acceleration(self, product_type: str, lookback_hours: int = 24) -> Optional[Dict]:
        """
        Detect when freshness scores drop faster than normal
        """
        query = f"""
            SELECT
                fruit_type,
                AVG(freshness_score) as avg_freshness,
                MIN(freshness_score) as min_freshness,
                MAX(freshness_score) as max_freshness,
                COUNT(*) as sample_count,
                STDDEV(freshness_score) as freshness_stddev,
                AVG(blemish_count) as avg_blemishes
            FROM INVENTORY_DATA.FRESHNESS_SCORES
            WHERE fruit_type = '{product_type}'
            AND detection_timestamp >= DATEADD(hour, -{lookback_hours}, CURRENT_TIMESTAMP())
            GROUP BY fruit_type
        """

        print(f"🔍 Analyzing decay acceleration for {product_type}...")

        self.sf.connect()
        results = self.sf.execute_query(query)
        self.sf.close()

        if not results or len(results) == 0:
            return None

        current_data = results[0]
        avg_freshness = current_data.get('avg_freshness', 0)

        # Get historical baseline
        baseline_query = f"""
            SELECT AVG(freshness_score) as baseline_freshness
            FROM INVENTORY_DATA.FRESHNESS_SCORES
            WHERE fruit_type = '{product_type}'
            AND detection_timestamp BETWEEN
                DATEADD(day, -30, CURRENT_TIMESTAMP())
                AND DATEADD(day, -7, CURRENT_TIMESTAMP())
        """

        self.sf.connect()
        baseline_results = self.sf.execute_query(baseline_query)
        self.sf.close()

        if baseline_results and len(baseline_results) > 0:
            baseline_freshness = baseline_results[0].get('baseline_freshness', avg_freshness)
            acceleration_factor = baseline_freshness / max(avg_freshness, 1)

            if acceleration_factor >= 2.0:
                # Calculate units at risk
                units_query = f"""
                    SELECT COUNT(*) as units_at_risk
                    FROM INVENTORY_DATA.FRESHNESS_SCORES
                    WHERE fruit_type = '{product_type}'
                    AND freshness_score < 50
                    AND detection_timestamp >= DATEADD(hour, -{lookback_hours}, CURRENT_TIMESTAMP())
                """

                self.sf.connect()
                units_results = self.sf.execute_query(units_query)
                self.sf.close()

                units_at_risk = units_results[0].get('units_at_risk', 0) if units_results else 0

                signal = {
                    "type": "decay_acceleration",
                    "product": product_type,
                    "severity": "urgent" if acceleration_factor > 3.5 else "warning",
                    "confidence": min(0.9, 0.6 + (acceleration_factor / 10)),
                    "detected_at": datetime.now().isoformat(),
                    "metrics": {
                        "acceleration_factor": round(acceleration_factor, 2),
                        "current_avg_freshness": round(avg_freshness, 2),
                        "normal_avg_freshness": round(baseline_freshness, 2),
                        "units_at_risk": units_at_risk,
                        "sample_count": current_data.get('sample_count', 0)
                    }
                }

                return signal

        return None

    def detect_purchase_anomaly(self, product_type: str, lookback_days: int = 7) -> Optional[Dict]:
        """
        Detect sudden drops in customer purchases
        """
        query = f"""
            SELECT
                DATE(purchase_date) as purchase_day,
                COUNT(*) as purchase_count,
                SUM(quantity) as total_quantity,
                SUM(unit_price * quantity) as total_revenue
            FROM RAW_DATA.PURCHASE_HISTORY
            WHERE product_name LIKE '%{product_type}%'
            AND purchase_date >= DATEADD(day, -{lookback_days * 2}, CURRENT_TIMESTAMP())
            GROUP BY DATE(purchase_date)
            ORDER BY purchase_day DESC
        """

        print(f"🔍 Analyzing purchase patterns for {product_type}...")

        self.sf.connect()
        results = self.sf.execute_query(query)
        self.sf.close()

        if not results or len(results) < lookback_days:
            return None

        # Split into current week and previous week
        current_week = results[:lookback_days]
        previous_week = results[lookback_days:lookback_days*2]

        current_purchases = sum(r.get('purchase_count', 0) for r in current_week)
        previous_purchases = sum(r.get('purchase_count', 0) for r in previous_week)

        if previous_purchases > 0:
            drop_percent = ((previous_purchases - current_purchases) / previous_purchases) * 100

            if drop_percent >= 40:
                # Check inventory at risk
                inventory_query = f"""
                    SELECT
                        COUNT(*) as inventory_count,
                        AVG(freshness_score) as avg_freshness
                    FROM INVENTORY_DATA.FRESHNESS_SCORES
                    WHERE fruit_type = '{product_type}'
                    AND detection_timestamp >= DATEADD(day, -1, CURRENT_TIMESTAMP())
                """

                self.sf.connect()
                inventory_results = self.sf.execute_query(inventory_query)
                self.sf.close()

                inventory_at_risk = inventory_results[0].get('inventory_count', 0) if inventory_results else 0
                avg_price = 2.0  # Default estimate

                signal = {
                    "type": "purchase_anomaly",
                    "product": product_type,
                    "severity": "urgent" if drop_percent > 60 else "warning",
                    "confidence": min(0.95, 0.65 + (drop_percent / 200)),
                    "detected_at": datetime.now().isoformat(),
                    "metrics": {
                        "purchase_drop_percent": round(drop_percent, 1),
                        "current_week_purchases": current_purchases,
                        "previous_week_purchases": previous_purchases,
                        "inventory_at_risk": inventory_at_risk,
                        "estimated_loss": round(inventory_at_risk * avg_price, 2)
                    }
                }

                return signal

        return None

    def detect_weather_impact(self, location: str = "default") -> Optional[Dict]:
        """
        Correlate weather forecasts with purchasing patterns
        """
        import requests
        from config import WEATHER_API_KEY, WEATHER_API_URL

        print(f"🌤️  Analyzing weather impact for {location}...")

        try:
            # Fetch current weather and forecast
            weather_url = f"{WEATHER_API_URL}/forecast?q={location}&appid={WEATHER_API_KEY}&units=imperial"
            response = requests.get(weather_url, timeout=5)

            if response.status_code == 200:
                weather_data = response.json()
                forecast = weather_data.get('list', [])[0]
                temp = forecast.get('main', {}).get('temp', 70)

                # Analyze temperature impact on demand
                demand_shifts = {}
                if temp > 85:
                    demand_shifts = {
                        "berries": +45,
                        "leafy_greens": -30,
                        "melons": +60,
                        "hot_beverages": -70
                    }
                    event = "heatwave"
                elif temp < 40:
                    demand_shifts = {
                        "citrus": +30,
                        "root_vegetables": +25,
                        "salad_greens": -40
                    }
                    event = "cold_snap"
                else:
                    return None

                signal = {
                    "type": "weather_pattern",
                    "location": location,
                    "severity": "info",
                    "confidence": 0.73,
                    "detected_at": datetime.now().isoformat(),
                    "metrics": {
                        "weather_event": event,
                        "temperature_forecast": round(temp, 1),
                        "predicted_demand_shift": demand_shifts
                    }
                }

                return signal
        except Exception as e:
            print(f"⚠️  Weather API error: {e}")
            return None

    def detect_customer_behavior_break(self, customer_segment: str = "regular") -> Optional[Dict]:
        """
        Identify when regular customers stop buying certain products
        """
        query = f"""
            WITH regular_customers AS (
                SELECT DISTINCT customer_id
                FROM RAW_DATA.PURCHASE_HISTORY
                WHERE purchase_date >= DATEADD(month, -3, CURRENT_TIMESTAMP())
                GROUP BY customer_id
                HAVING COUNT(*) >= 8
            ),
            recent_gaps AS (
                SELECT
                    ph.customer_id,
                    ph.product_name,
                    COUNT(*) as purchase_frequency,
                    MAX(ph.purchase_date) as last_purchase,
                    DATEDIFF(day, MAX(ph.purchase_date), CURRENT_TIMESTAMP()) as days_since_last
                FROM RAW_DATA.PURCHASE_HISTORY ph
                JOIN regular_customers rc ON ph.customer_id = rc.customer_id
                GROUP BY ph.customer_id, ph.product_name
                HAVING days_since_last > 14
            )
            SELECT
                product_name,
                COUNT(DISTINCT customer_id) as affected_customers,
                AVG(days_since_last) as avg_days_gap
            FROM recent_gaps
            GROUP BY product_name
            HAVING COUNT(DISTINCT customer_id) > 50
            ORDER BY affected_customers DESC
        """

        print(f"🔍 Analyzing customer behavior patterns for {customer_segment}...")

        self.sf.connect()
        results = self.sf.execute_query(query)
        self.sf.close()

        if not results or len(results) == 0:
            return None

        top_affected = results[0]
        affected_count = top_affected.get('affected_customers', 0)

        if affected_count >= 50:
            signal = {
                "type": "customer_behavior_break",
                "segment": customer_segment,
                "severity": "warning",
                "confidence": min(0.9, 0.7 + (affected_count / 500)),
                "detected_at": datetime.now().isoformat(),
                "metrics": {
                    "affected_customers": affected_count,
                    "products_affected": [r.get('product_name') for r in results[:3]],
                    "avg_gap_days": round(top_affected.get('avg_days_gap', 0), 1),
                    "potential_recovery_actions": [
                        "Match competitor pricing",
                        "Send targeted promotions",
                        "Launch loyalty program incentive"
                    ]
                }
            }

            return signal

        return None

    def analyze_all_signals(self) -> List[Dict]:
        """
        Run all signal detection algorithms
        """
        print("🚨 Running comprehensive signal analysis...")

        signals = []

        # Detect decay acceleration for common products
        for product in ["strawberries", "bananas", "avocados", "lettuce", "blueberries"]:
            try:
                signal = self.detect_decay_acceleration(product)
                if signal and signal["confidence"] > 0.7:
                    signals.append(signal)
            except Exception as e:
                print(f"⚠️  Error analyzing {product}: {e}")

        # Detect purchase anomalies
        for product in ["avocados", "berries", "leafy_greens", "organic_produce"]:
            try:
                signal = self.detect_purchase_anomaly(product)
                if signal and signal["confidence"] > 0.65:
                    signals.append(signal)
            except Exception as e:
                print(f"⚠️  Error analyzing purchases for {product}: {e}")

        # Weather impact
        try:
            weather_signal = self.detect_weather_impact()
            if weather_signal:
                signals.append(weather_signal)
        except Exception as e:
            print(f"⚠️  Error analyzing weather: {e}")

        # Customer behavior
        try:
            behavior_signal = self.detect_customer_behavior_break()
            if behavior_signal:
                signals.append(behavior_signal)
        except Exception as e:
            print(f"⚠️  Error analyzing customer behavior: {e}")

        print(f"✅ Detected {len(signals)} actionable signals")

        self.signals_detected = signals
        return signals

    def prioritize_signals(self, signals: List[Dict]) -> List[Dict]:
        """
        Sort signals by severity and confidence
        """
        severity_order = {"urgent": 3, "warning": 2, "info": 1}

        return sorted(
            signals,
            key=lambda s: (severity_order.get(s["severity"], 0), s["confidence"]),
            reverse=True
        )

    def get_signal_summary(self) -> str:
        """
        Generate human-readable summary of detected signals
        """
        if not self.signals_detected:
            return "No significant signals detected."

        summary = f"📊 Signal Analysis Summary\n"
        summary += f"Detected {len(self.signals_detected)} signals:\n\n"

        for i, signal in enumerate(self.signals_detected, 1):
            summary += f"{i}. {signal['type'].upper()} - {signal.get('product', signal.get('segment', 'N/A'))}\n"
            summary += f"   Severity: {signal['severity']} | Confidence: {signal['confidence']:.0%}\n"

        return summary
