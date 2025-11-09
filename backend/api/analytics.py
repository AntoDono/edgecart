"""
Enhanced Analytics API Endpoints
Provides comprehensive waste reduction and CO2 impact metrics
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.waste_impact import (
        calculate_impact_metrics,
        simulate_impact_for_item,
        get_time_series_impact
    )
    from models import db, FruitInventory, FreshnessStatus, WasteLog, Customer
    WASTE_IMPACT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Waste impact module not available: {e}")
    WASTE_IMPACT_AVAILABLE = False

try:
    from utils.markov_waste_estimator import (
        estimate_units_saved,
        estimate_co2e_saved,
        estimate_additional_revenue_generated,
        compute_aggregate_impact
    )
    MARKOV_ESTIMATOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Markov estimator module not available: {e}")
    MARKOV_ESTIMATOR_AVAILABLE = False

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/impact', methods=['GET'])
def get_impact_metrics():
    """
    Get comprehensive impact metrics
    
    Query params:
    - days: Number of days to analyze (default: 30)
    - store_id: Filter by store (optional)
    - start_date: Start date (ISO format, optional)
    - end_date: End date (ISO format, optional)
    """
    if not WASTE_IMPACT_AVAILABLE:
        return jsonify({'error': 'Waste impact module not available'}), 503
    
    try:
        days = int(request.args.get('days', 30))
        store_id = request.args.get('store_id', type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if start_date_str and end_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        else:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
        
        metrics = calculate_impact_metrics(start_date, end_date, store_id)
        
        # Add human-readable conversions
        metrics['waste_prevented_lbs'] = round(metrics['waste_prevented_kg'] * 2.20462, 2)
        metrics['co2_saved_lbs'] = round(metrics['co2_saved_kg'] * 2.20462, 2)
        metrics['co2_saved_tons'] = round(metrics['co2_saved_kg'] / 1000, 3)
        
        # Add equivalent comparisons (for demo impact)
        metrics['equivalent_cars_removed'] = round(metrics['co2_saved_kg'] / 4230, 2)  # Average car emits 4230 kg CO2/year
        metrics['equivalent_trees_planted'] = round(metrics['co2_saved_kg'] / 21.77, 0)  # Tree absorbs ~21.77 kg CO2/year
        
        return jsonify(metrics), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/impact/time-series', methods=['GET'])
def get_time_series():
    """
    Get time series data for impact visualization
    
    Query params:
    - days: Number of days (default: 30)
    - store_id: Filter by store (optional)
    """
    if not WASTE_IMPACT_AVAILABLE:
        return jsonify({'error': 'Waste impact module not available'}), 503
    
    try:
        days = int(request.args.get('days', 30))
        store_id = request.args.get('store_id', type=int)
        
        time_series = get_time_series_impact(days, store_id)
        
        return jsonify({
            'time_series': time_series,
            'days': days
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/impact/simulate/<int:inventory_id>', methods=['GET'])
def simulate_item_impact(inventory_id):
    """
    Simulate potential impact if an item is discounted
    
    Query params:
    - discount: Discount percentage to simulate (optional, uses current if not provided)
    """
    if not WASTE_IMPACT_AVAILABLE:
        return jsonify({'error': 'Waste impact module not available'}), 503
    
    try:
        item = FruitInventory.query.get(inventory_id)
        if not item:
            return jsonify({'error': 'Item not found'}), 404
        
        discount = request.args.get('discount', type=float)
        if discount is None:
            if item.freshness:
                discount = item.freshness.discount_percentage
            else:
                discount = 0.0
        
        # Calculate days until expiry
        days_until_expiry = 0
        if item.freshness and item.freshness.predicted_expiry_date:
            days_until_expiry = (item.freshness.predicted_expiry_date - datetime.utcnow()).days
        
        simulation = simulate_impact_for_item(inventory_id, discount, days_until_expiry)
        
        return jsonify(simulation), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/waste', methods=['GET'])
def get_waste_analytics():
    """
    Enhanced waste analytics (backward compatible with existing endpoint)
    """
    try:
        days = int(request.args.get('days', 30))
        store_id = request.args.get('store_id', type=int)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get comprehensive metrics
        metrics = calculate_impact_metrics(start_date, end_date, store_id)
        
        # Also include legacy format for backward compatibility
        waste_logs = WasteLog.query.filter(
            WasteLog.logged_at >= start_date,
            WasteLog.logged_at <= end_date
        ).all()
        
        if store_id:
            waste_logs = [w for w in waste_logs if w.inventory and w.inventory.store_id == store_id]
        
        return jsonify({
            # Legacy format
            'total_wasted': sum(log.quantity_wasted for log in waste_logs),
            'total_value_loss': sum(log.estimated_value_loss or 0 for log in waste_logs),
            'waste_logs': [log.to_dict() for log in waste_logs[:10]],
            
            # Enhanced metrics
            'waste_prevented_kg': metrics['waste_prevented_kg'],
            'waste_prevented_lbs': round(metrics['waste_prevented_kg'] * 2.20462, 2),
            'co2_saved_kg': metrics['co2_saved_kg'],
            'co2_saved_lbs': round(metrics['co2_saved_kg'] * 2.20462, 2),
            'waste_reduction_percentage': metrics['waste_reduction_percentage'],
            'revenue_recovered': metrics['revenue_recovered'],
            'items_saved': metrics['items_saved']
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/v1/metrics/recompute', methods=['POST'])
def recompute_lot_metrics():
    """
    Recomputes waste reduction and CO2e savings for a specific inventory lot
    using the Personalized Buy-Probability + Markov Estimator.
    
    Query params:
    - lot_id: ID of the FruitInventory item (required)
    - user_id: Optional. If provided, uses specific user stats. Otherwise, uses first customer.
    """
    if not MARKOV_ESTIMATOR_AVAILABLE:
        return jsonify({'error': 'Markov estimator module not available'}), 503
    
    try:
        lot_id = request.args.get('lot_id', type=int)
        if not lot_id:
            return jsonify({'error': 'lot_id is required'}), 400

        from models import FruitInventory, Customer
        
        inventory_item = FruitInventory.query.get(lot_id)
        if not inventory_item:
            return jsonify({'error': f'Inventory item with ID {lot_id} not found'}), 404

        # Determine user_id for personalized calculations
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            # Fallback to first customer if no user_id provided
            default_customer = Customer.query.first()
            if not default_customer:
                return jsonify({'error': 'No customers found to perform personalized calculations'}), 500
            user_id = default_customer.id

        # Define baseline and dynamic pricing parameters
        # Baseline policy: {dmax:0.0, alpha:1.0} (no discount)
        baseline_params = {"dmax": 0.0, "alpha": 1.0}
        
        # Dynamic policy: Use the system's current discount parameters
        dynamic_params = {"dmax": 0.75, "alpha": 1.5}  # Max 75% discount, power 1.5 curve

        # Estimate units saved
        units_saved = estimate_units_saved(
            lot_id=lot_id,
            baseline_params=baseline_params,
            dynamic_params=dynamic_params,
            user_id=user_id
        )

        # Estimate CO2e saved
        product_name = inventory_item.fruit_type
        co2e_saved = estimate_co2e_saved(units_saved, product_name)

        # Estimate additional revenue generated
        avg_price_per_unit = inventory_item.current_price if inventory_item.current_price > 0 else inventory_item.original_price
        additional_revenue_generated = estimate_additional_revenue_generated(
            units_saved,
            product_name,
            avg_price_per_unit
        )

        return jsonify({
            'lot_id': lot_id,
            'units_saved': round(units_saved, 2),
            'co2e_saved': round(co2e_saved, 2),
            'additional_revenue_generated': round(additional_revenue_generated, 2),
            'assumptions': {
                'baseline_policy': baseline_params,
                'dynamic_policy': dynamic_params,
                'user_id_for_calculation': user_id
            }
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/v1/metrics/detailed', methods=['GET'])
def get_detailed_metrics():
    """
    Get detailed impact metrics with per-item breakdown and calculation details.
    
    Query params:
    - store_id: Optional store ID to filter by
    - user_id: Optional user ID (uses first customer if not provided)
    """
    if not MARKOV_ESTIMATOR_AVAILABLE:
        return jsonify({'error': 'Markov estimator module not available'}), 503
    
    try:
        store_id = request.args.get('store_id', type=int)
        user_id = request.args.get('user_id', type=int)
        
        # Get aggregate metrics
        metrics = compute_aggregate_impact(store_id=store_id, user_id=user_id)
        
        # Get per-item breakdown
        from models import FruitInventory, Customer
        from utils.markov_waste_estimator import (
            estimate_units_saved,
            estimate_co2e_saved,
            estimate_additional_revenue_generated
        )
        
        # Default parameters
        baseline_params = {"dmax": 0.0, "alpha": 1.0}
        dynamic_params = {"dmax": 0.75, "alpha": 1.5}
        
        # Get user_id
        if user_id is None:
            default_customer = Customer.query.first()
            if not default_customer:
                return jsonify({'error': 'No customer found in database'}), 400
            user_id = default_customer.id
        
        # Query inventory
        query = FruitInventory.query.filter(FruitInventory.quantity > 0)
        if store_id:
            query = query.filter(FruitInventory.store_id == store_id)
        
        inventory_items = query.all()
        
        item_breakdown = []
        for item in inventory_items:
            try:
                units = estimate_units_saved(
                    item.id,
                    baseline_params,
                    dynamic_params,
                    user_id
                )
                
                if units > 0:
                    co2e = estimate_co2e_saved(units, item.fruit_type)
                    revenue = estimate_additional_revenue_generated(
                        units,
                        item.fruit_type,
                        item.current_price if item.current_price > 0 else item.original_price
                    )
                    
                    # Get freshness score
                    freshness_score = None
                    if item.freshness:
                        freshness_score = item.freshness.freshness_score
                        if freshness_score > 1.0:
                            freshness_score = freshness_score / 100.0
                    
                    item_breakdown.append({
                        'inventory_id': item.id,
                        'fruit_type': item.fruit_type,
                        'quantity': item.quantity,
                        'freshness_score': freshness_score,
                        'units_saved': round(units, 2),
                        'co2e_saved': round(co2e, 2),
                        'revenue_generated': round(revenue, 2)
                    })
            except Exception as e:
                print(f"Error processing item {item.id} for detailed analytics: {e}")
                continue
        
        # Add human-readable conversions
        metrics['waste_saved_lbs'] = round(metrics.get('waste_saved_kg', metrics['units_saved']) * 2.20462, 2)
        metrics['co2e_saved_lbs'] = round(metrics['co2e_saved'] * 2.20462, 2)
        metrics['co2e_saved_tons'] = round(metrics['co2e_saved'] / 1000, 3)
        
        # Add detailed information
        result = {
            **metrics,
            'item_breakdown': item_breakdown,
            'calculations': {
                'method': 'Markov Chain Model with Personalized Buy-Probability',
                'baseline_policy': baseline_params,
                'dynamic_policy': dynamic_params,
                'user_id': user_id,
                'total_items_analyzed': len(inventory_items),
                'items_contributing': len(item_breakdown)
            },
            'assumptions': {
                'baseline_policy_description': 'No discount policy - items sold at full price',
                'dynamic_policy_description': 'Dynamic pricing based on freshness - up to 75% discount',
                'markov_chain_buckets': 48,
                'time_per_bucket_hours': 1.0,
                'note': 'Calculations compare probability of sale under dynamic vs baseline pricing'
            }
        }
        
        return jsonify(result), 200
    
    except Exception as e:
        import traceback
        print(f"❌ [Analytics] Error computing detailed metrics: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/v1/metrics/aggregate', methods=['GET'])
def get_aggregate_metrics():
    """
    Get aggregate impact metrics across all inventory using Markov estimator.
    
    Query params:
    - store_id: Optional store ID to filter by
    - user_id: Optional user ID (uses first customer if not provided)
    """
    if not MARKOV_ESTIMATOR_AVAILABLE:
        return jsonify({'error': 'Markov estimator module not available'}), 503
    
    try:
        store_id = request.args.get('store_id', type=int)
        user_id = request.args.get('user_id', type=int)
        
        # Debug logging
        print(f"🔍 [Analytics] Computing aggregate metrics - store_id: {store_id}, user_id: {user_id}")
        
        metrics = compute_aggregate_impact(store_id=store_id, user_id=user_id)
        
        print(f"🔍 [Analytics] Metrics computed: {metrics}")
        
        # Add human-readable conversions
        metrics['waste_saved_lbs'] = round(metrics.get('waste_saved_kg', metrics['units_saved']) * 2.20462, 2)
        metrics['co2e_saved_lbs'] = round(metrics['co2e_saved'] * 2.20462, 2)
        metrics['co2e_saved_tons'] = round(metrics['co2e_saved'] / 1000, 3)
        
        return jsonify(metrics), 200
    
    except Exception as e:
        import traceback
        print(f"❌ [Analytics] Error computing aggregate metrics: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

