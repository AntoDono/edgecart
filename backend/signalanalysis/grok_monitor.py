"""
Grok-Powered Real-Time Monitoring Agent
Continuously monitors Snowflake for waste signals and uses Grok for root cause analysis
"""

import time
from datetime import datetime
from typing import Dict, List
import json
import requests

from signal_detector import SignalDetector
from config import (
    XAI_API_KEY,
    XAI_API_BASE,
    GROK_MODEL,
    MONITORING_INTERVAL,
    LOOKBACK_HOURS,
    ALERT_THRESHOLD_URGENT,
    ALERT_THRESHOLD_WARNING,
    ENABLE_ALERTS,
    ALERT_SLACK_WEBHOOK
)


class GrokMonitor:
    """
    Real-time monitoring agent using Grok for intelligent waste prediction
    """

    def __init__(self, snowflake_connector):
        self.sf = snowflake_connector
        self.detector = SignalDetector(snowflake_connector)
        self.api_key = XAI_API_KEY
        self.api_base = XAI_API_BASE
        self.model = GROK_MODEL
        self.monitoring = False
        self.total_predictions = 0
        self.successful_interventions = 0

    def query_grok(self, prompt: str, context: Dict = None, temperature: float = 0.7) -> str:
        """
        Query Grok API for reasoning and analysis
        """
        print(f"🤖 Querying Grok ({self.model})...")

        # Build context-aware prompt
        full_prompt = prompt
        if context:
            context_str = json.dumps(context, indent=2)
            full_prompt = f"Context:\n{context_str}\n\nAnalysis Request:\n{prompt}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert grocery waste prevention analyst. Analyze signals, identify root causes, predict waste, and provide actionable recommendations."
                },
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": 1000
        }

        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                grok_response = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                return grok_response
            else:
                print(f"⚠️  Grok API error: {response.status_code}")
                return "Error: Unable to get Grok analysis"

        except Exception as e:
            print(f"❌ Grok API request failed: {e}")
            return f"Error: {str(e)}"

    def analyze_signal_with_grok(self, signal: Dict) -> Dict:
        """
        Use Grok to perform root cause analysis on detected signal
        """
        print(f"\n🔬 Analyzing signal: {signal['type']} - {signal.get('product', 'N/A')}")

        # Build detailed analysis prompt
        metrics_summary = "\n".join([f"  - {k}: {v}" for k, v in signal.get('metrics', {}).items()])

        prompt = f"""
Analyze this grocery waste signal and provide a structured response:

Signal Type: {signal['type']}
Product: {signal.get('product', 'N/A')}
Severity: {signal['severity']}
Confidence: {signal['confidence']:.0%}

Metrics:
{metrics_summary}

Provide your analysis in this format:
1. ROOT CAUSES (2-3 specific factors)
2. WASTE PREDICTION (units, dollars, timeframe)
3. RECOMMENDED ACTIONS (3-4 prioritized steps with urgency levels)
4. PREVENTION STRATEGY (how to avoid this in the future)
"""

        # Get Grok's reasoning
        grok_response = self.query_grok(prompt, context=signal)

        # Parse Grok's response and structure it
        enhanced_signal = {
            **signal,
            "grok_analysis": {
                "full_analysis": grok_response,
                "analyzed_at": datetime.now().isoformat(),
                "model_used": self.model
            }
        }

        self.total_predictions += 1
        return enhanced_signal

    def generate_alert(self, enhanced_signal: Dict) -> str:
        """
        Generate human-readable alert from analyzed signal
        """
        severity_emoji = {
            "urgent": "🚨",
            "warning": "⚠️",
            "info": "ℹ️"
        }

        emoji = severity_emoji.get(enhanced_signal["severity"], "📊")
        product = enhanced_signal.get("product", enhanced_signal.get("segment", "Unknown"))
        signal_type = enhanced_signal["type"].replace("_", " ").title()

        alert = f"\n{'='*70}\n"
        alert += f"{emoji} {enhanced_signal['severity'].upper()}: {signal_type} - {product}\n"
        alert += f"{'='*70}\n"
        alert += f"Confidence: {enhanced_signal['confidence']:.0%}\n"
        alert += f"Detected: {enhanced_signal['detected_at']}\n\n"

        # Metrics summary
        alert += "📊 Key Metrics:\n"
        for key, value in enhanced_signal.get("metrics", {}).items():
            formatted_key = key.replace("_", " ").title()
            alert += f"  • {formatted_key}: {value}\n"

        # Grok's analysis
        if "grok_analysis" in enhanced_signal:
            analysis = enhanced_signal["grok_analysis"]
            alert += f"\n🤖 Grok Analysis ({self.model}):\n"
            alert += f"{analysis['full_analysis']}\n"

        alert += f"\n{'='*70}\n"

        return alert

    def send_slack_alert(self, alert_text: str):
        """
        Send alert to Slack webhook
        """
        if not ENABLE_ALERTS:
            return

        try:
            payload = {
                "text": alert_text,
                "username": "EdgeCart Waste Monitor",
                "icon_emoji": ":warning:"
            }

            response = requests.post(
                ALERT_SLACK_WEBHOOK,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                print("✅ Alert sent to Slack")
            else:
                print(f"⚠️  Slack webhook failed: {response.status_code}")

        except Exception as e:
            print(f"⚠️  Could not send Slack alert: {e}")

    def process_natural_language_query(self, query: str) -> str:
        """
        Allow managers to query Grok directly about waste patterns
        """
        print(f"\n💬 Manager query: \"{query}\"")

        # Build context from recent signals and Snowflake data
        context = {
            "recent_signals": [
                {
                    "type": s["type"],
                    "product": s.get("product", s.get("segment")),
                    "severity": s["severity"],
                    "detected_at": s["detected_at"]
                }
                for s in self.detector.signals_detected[-10:]
            ],
            "timestamp": datetime.now().isoformat(),
            "warehouse": "Snowflake EDGECART_DB"
        }

        # Query Grok with context
        response = self.query_grok(query, context=context, temperature=0.8)

        return response

    def monitor_cycle(self):
        """
        Run single monitoring cycle
        """
        print(f"\n{'='*70}")
        print(f"🔄 Monitoring Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")
        print(f"Cycle #{self.total_predictions + 1} | Total predictions: {self.total_predictions}")

        # Detect signals from Snowflake
        signals = self.detector.analyze_all_signals()

        # Prioritize by severity and confidence
        prioritized = self.detector.prioritize_signals(signals)

        # Analyze urgent/warning signals with Grok
        alerts_sent = 0
        for signal in prioritized:
            if signal["confidence"] >= ALERT_THRESHOLD_WARNING:
                # Get Grok's analysis
                enhanced = self.analyze_signal_with_grok(signal)

                # Generate alert
                alert = self.generate_alert(enhanced)
                print(alert)

                # Send to Slack if urgent
                if signal["severity"] == "urgent" and signal["confidence"] >= ALERT_THRESHOLD_URGENT:
                    self.send_slack_alert(alert)
                    alerts_sent += 1

        print(f"\n📈 Cycle Summary:")
        print(f"  • Signals detected: {len(signals)}")
        print(f"  • High-confidence signals: {len(prioritized)}")
        print(f"  • Alerts sent: {alerts_sent}")
        print(f"\n✅ Monitoring cycle complete")
        print(f"Next check in {MONITORING_INTERVAL} seconds...")

    def start_monitoring(self):
        """
        Start continuous monitoring loop
        """
        print("="*70)
        print("🚀 STARTING GROK-POWERED WASTE DETECTION SYSTEM")
        print("="*70)
        print(f"   Model: {self.model}")
        print(f"   Interval: {MONITORING_INTERVAL}s ({MONITORING_INTERVAL // 60} minutes)")
        print(f"   Lookback window: {LOOKBACK_HOURS}h")
        print(f"   Data source: Snowflake EDGECART_DB")
        print(f"   Alerts: {'Enabled' if ENABLE_ALERTS else 'Disabled'}")
        print("="*70)

        self.monitoring = True

        try:
            while self.monitoring:
                self.monitor_cycle()
                time.sleep(MONITORING_INTERVAL)
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped by user")
            print(f"Total predictions made: {self.total_predictions}")
            self.monitoring = False

    def stop_monitoring(self):
        """
        Stop monitoring loop
        """
        self.monitoring = False
        print(f"🛑 Monitoring stopped")
        print(f"Session statistics:")
        print(f"  • Total predictions: {self.total_predictions}")
        print(f"  • Successful interventions: {self.successful_interventions}")


def main():
    """
    Main entry point for Grok monitoring agent
    """
    import sys
    sys.path.append('../snowflake')

    from snowflake_connector import get_snowflake_connector

    # Initialize Snowflake connection
    print("📊 Initializing Snowflake connection...")
    sf = get_snowflake_connector()
    sf.schema = "INVENTORY_DATA"

    # Create monitor
    monitor = GrokMonitor(sf)

    # Check if running in demo mode or continuous mode
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        print("\n" + "="*70)
        print("DEMO MODE: Natural Language Interface")
        print("="*70)

        # Example query
        response = monitor.process_natural_language_query(
            "Why did strawberry waste spike yesterday?"
        )
        print(f"\n🤖 Grok Response:\n{response}\n")

        # Single monitoring cycle
        print("\n" + "="*70)
        print("DEMO MODE: Single Monitoring Cycle")
        print("="*70)
        monitor.monitor_cycle()

    else:
        # Start continuous monitoring
        monitor.start_monitoring()


if __name__ == "__main__":
    main()
