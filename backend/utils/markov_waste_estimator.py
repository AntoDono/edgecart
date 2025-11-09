"""
Personalized Buy-Probability + Markov Estimator
Estimates units saved and CO2e avoided using blended population/user buy probabilities
and absorbing Markov chain modeling.
"""
import numpy as np
from typing import Callable, Dict, Tuple, Optional
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from models import db, FruitInventory, FreshnessStatus, Customer, PriceCurve, UserDiscountStat, ProductLCA
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Models not available: {e}")
    MODELS_AVAILABLE = False


def calculate_discount_from_freshness(freshness_score: float, max_discount: float = 0.75, power: float = 1.5) -> float:
    """
    Calculates discount percentage based on freshness score.
    Replicates FreshnessStatus.calculate_discount() logic.
    
    Args:
        freshness_score: Freshness score (0.0 to 1.0)
        max_discount: Maximum discount at 0 freshness (default 0.75 for 75%)
        power: Power factor controlling curve shape (default 1.5)
    
    Returns:
        Discount as float between 0.0 and max_discount
    """
    if not (0.0 <= freshness_score <= 1.0):
        raise ValueError("Freshness score must be between 0.0 and 1.0")
    
    # Ensure max_discount is a ratio (e.g., 0.75 for 75%)
    if max_discount > 1.0:
        max_discount /= 100.0

    discount = max_discount * (1 - (freshness_score ** power))
    return max(0.0, min(max_discount, discount))


def p_buy_pop_interp(discount_pct: float, category: str) -> float:
    """
    Interpolates population buy probability from stored price curves.
    
    Args:
        discount_pct: Discount percentage (0-100)
        category: Product category (e.g., 'apple', 'banana')
    
    Returns:
        Buy probability (0.0 to 1.0)
    """
    if not MODELS_AVAILABLE:
        # Fallback: simple linear approximation
        return min(0.9, 0.05 + (discount_pct / 100.0) * 0.85)
    
    price_curve = PriceCurve.query.filter_by(category=category).first()
    if not price_curve:
        # Fallback: default probability based on discount
        return min(0.9, 0.05 + (discount_pct / 100.0) * 0.85)
    
    bins = price_curve.x_discount_bins
    probs = price_curve.y_pbuy
    
    if not bins or not probs or len(bins) != len(probs):
        return 0.05  # Default low probability
    
    return float(np.interp(discount_pct, bins, probs, left=probs[0] if probs else 0.05, right=probs[-1] if probs else 0.9))


def p_buy_user_beta(user_id: int, product_name: str, discount_pct: float) -> Tuple[float, int]:
    """
    Computes user-specific buy probability using Beta posterior mean.
    
    Args:
        user_id: Customer ID
        product_name: Product name (e.g., 'apple')
        discount_pct: Discount percentage (0-100)
    
    Returns:
        Tuple of (probability, total_trials)
    """
    if not MODELS_AVAILABLE:
        return 0.0, 0
    
    user_stats = UserDiscountStat.query.filter_by(
        user_id=user_id,
        product_name=product_name
    ).all()
    
    # Find matching bins
    matches = [r for r in user_stats if r.bin_low <= discount_pct < r.bin_high]
    trials = sum(r.trials for r in matches)
    buys = sum(r.buys for r in matches)
    
    if trials == 0:
        return 0.0, 0
    
    # Beta posterior mean: (buys + 1) / (trials + 2)
    return (buys + 1) / (trials + 2), trials


def p_buy_blend(user_id: int, product_name: str, category: str, discount_pct: float, m: int = 15) -> float:
    """
    Blends population and user-specific buy probabilities.
    
    Args:
        user_id: Customer ID
        product_name: Product name
        category: Product category (same as product_name for simplicity)
        discount_pct: Discount percentage (0-100)
        m: Blending parameter (default 15)
    
    Returns:
        Blended buy probability (0.0 to 1.0)
    """
    p_pop = p_buy_pop_interp(discount_pct, category)
    p_user, n = p_buy_user_beta(user_id, product_name, discount_pct)
    
    if n == 0:
        return p_pop
    
    # Weighted blend: w = n / (n + m)
    w = n / (n + m)
    return w * p_user + (1 - w) * p_pop


def sold_prob_markov(
    freshness: float,
    dmax: float,
    alpha: float,
    K: int,
    dt_hours: float,
    user_id: int,
    product_name: str,
    category: str
) -> float:
    """
    Computes the probability of an item being sold using an absorbing Markov chain.
    
    Args:
        freshness: Current freshness score (0.0 to 1.0)
        dmax: Maximum discount (0.0 to 1.0, e.g., 0.75 for 75%)
        alpha: Power factor for discount curve
        K: Number of freshness buckets (e.g., 48 for 48 hours if dt_hours=1)
        dt_hours: Duration of each freshness bucket in hours
        user_id: Customer ID for personalized buy probability
        product_name: Product name
        category: Product category
    
    Returns:
        Probability of being sold (0.0 to 1.0)
    """
    # k0 is the starting freshness bucket (1-indexed)
    k0 = int((1 - max(0.0, min(1.0, freshness))) * K) + 1
    k0 = min(k0, K)  # Ensure k0 does not exceed K
    
    Q = np.zeros((K, K))  # Transition matrix for transient states
    R = np.zeros((K, 2))  # Transition matrix to absorbing states (Sold, Spoiled)
    
    for k in range(1, K + 1):
        # Freshness for this bucket (1.0 at k=1, approaches 0 at k=K)
        Fk = 1.0 - (k - 1) / K
        
        # Calculate discount for this freshness level
        dk = calculate_discount_from_freshness(Fk, max_discount=dmax, power=alpha)
        dk_pct = dk * 100.0  # Convert to percentage for p_buy functions
        
        # Get blended buy probability
        p = p_buy_blend(user_id, product_name, category, dk_pct)
        
        if k < K:
            # Transition to next freshness bucket (not sold)
            Q[k - 1, k] = 1 - p
            # Transition to Sold state
            R[k - 1, 0] = p
        else:
            # Last bucket (F_K) - must transition to absorbing state
            R[k - 1, 0] = p  # Sold
            R[k - 1, 1] = 1 - p  # Spoiled (not sold in last bucket)
    
    # Fundamental matrix N = (I - Q)^-1
    I = np.eye(K)
    try:
        N = np.linalg.inv(I - Q)
    except np.linalg.LinAlgError:
        # Handle singular matrix case
        return 0.0
    
    # Absorbing probabilities B = N * R
    B = N @ R
    
    # Probability of being sold starting from k0
    return float(B[k0 - 1, 0])  # Index 0 for Sold state


def estimate_units_saved(
    lot_id: int,
    baseline_params: Dict[str, float],
    dynamic_params: Dict[str, float],
    user_id: int,
    K: int = 48,
    dt_hours: float = 1.0
) -> float:
    """
    Estimates units saved for a given inventory lot by comparing dynamic vs baseline pricing.
    
    Args:
        lot_id: Inventory item ID
        baseline_params: {'dmax': float, 'alpha': float} for baseline policy
        dynamic_params: {'dmax': float, 'alpha': float} for dynamic policy
        user_id: Customer ID for personalized calculations
        K: Number of freshness buckets (default 48)
        dt_hours: Duration of each bucket in hours (default 1.0)
    
    Returns:
        Estimated units saved
    """
    if not MODELS_AVAILABLE:
        return 0.0
    
    inventory_item = FruitInventory.query.get(lot_id)
    if not inventory_item:
        return 0.0
    
    # Get current freshness (0-1.0 scale)
    # Note: FreshnessStatus stores freshness_score as 0-1.0, but we handle both scales
    if inventory_item.freshness:
        freshness_score = inventory_item.freshness.freshness_score
        # Convert from 0-100 scale to 0-1.0 if needed
        if freshness_score > 1.0:
            freshness_score = freshness_score / 100.0
        current_freshness = max(0.0, min(1.0, freshness_score))
    else:
        # Default to fresh if no freshness data
        current_freshness = 1.0
    
    product_name = inventory_item.fruit_type
    category = product_name  # Simplification: category is same as product_name
    
    # Calculate sold probability with dynamic pricing
    ps_dyn = sold_prob_markov(
        current_freshness,
        dynamic_params["dmax"],
        dynamic_params["alpha"],
        K,
        dt_hours,
        user_id,
        product_name,
        category
    )
    
    # Calculate sold probability with baseline pricing
    ps_base = sold_prob_markov(
        current_freshness,
        baseline_params["dmax"],
        baseline_params["alpha"],
        K,
        dt_hours,
        user_id,
        product_name,
        category
    )
    
    # Units saved = quantity * (probability difference)
    units_saved = max(0.0, inventory_item.quantity * (ps_dyn - ps_base))
    
    # Debug logging for items with zero units saved
    if units_saved == 0.0 and inventory_item.quantity > 0:
        print(f"  ⚠️ Item {lot_id} ({product_name}): qty={inventory_item.quantity}, freshness={current_freshness:.3f}, ps_dyn={ps_dyn:.3f}, ps_base={ps_base:.3f}, diff={ps_dyn-ps_base:.3f}")
    
    return units_saved


def estimate_co2e_saved(units_saved: float, product_name: str) -> float:
    """
    Estimates CO2e saved based on units saved and product LCA data.
    
    Args:
        units_saved: Number of units saved from waste
        product_name: Product name (e.g., 'apple')
    
    Returns:
        CO2e saved in kg
    """
    if not MODELS_AVAILABLE or units_saved <= 0:
        return 0.0
    
    product_lca = ProductLCA.query.filter_by(product_name=product_name).first()
    if not product_lca:
        # Fallback: use default values from waste_impact.py
        from utils.waste_impact import get_emission_factor, get_average_weight
        emission_factor = get_emission_factor(product_name)
        mass_kg = get_average_weight(product_name)
        co2e_per_unit = mass_kg * emission_factor
        return units_saved * co2e_per_unit
    
    # CO2e per unit = displacement * mass * production_ef + disposal_ef
    co2e_per_unit = (
        product_lca.displacement * product_lca.mass_kg * product_lca.ef_prod_kgco2e_perkg +
        product_lca.ef_disposal_kgco2e_perunit
    )
    
    return units_saved * co2e_per_unit


def estimate_additional_revenue_generated(units_saved: float, product_name: str, avg_price_per_unit: float) -> float:
    """
    Estimates additional revenue generated from units saved.
    Simplified calculation assuming units are sold at average price.
    
    Args:
        units_saved: Number of units saved
        product_name: Product name
        avg_price_per_unit: Average price per unit
    
    Returns:
        Additional revenue in dollars
    """
    return units_saved * avg_price_per_unit


def compute_aggregate_impact(
    store_id: Optional[int] = None,
    user_id: Optional[int] = None,
    baseline_params: Optional[Dict[str, float]] = None,
    dynamic_params: Optional[Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Computes aggregate impact metrics across all inventory items.
    
    Args:
        store_id: Optional store ID to filter by
        user_id: Optional user ID (uses first customer if not provided)
        baseline_params: Baseline pricing parameters
        dynamic_params: Dynamic pricing parameters
    
    Returns:
        Dictionary with 'units_saved', 'co2e_saved', 'revenue_generated'
    """
    if not MODELS_AVAILABLE:
        print("⚠️ [Markov Estimator] MODELS_AVAILABLE is False")
        return {'units_saved': 0.0, 'co2e_saved': 0.0, 'revenue_generated': 0.0, 'waste_saved_kg': 0.0}
    
    # Default parameters
    if baseline_params is None:
        baseline_params = {"dmax": 0.0, "alpha": 1.0}  # No discount baseline
    if dynamic_params is None:
        dynamic_params = {"dmax": 0.75, "alpha": 1.5}  # Current system parameters
    
    # Get user_id
    if user_id is None:
        default_customer = Customer.query.first()
        if not default_customer:
            print("⚠️ [Markov Estimator] No customer found in database")
            return {'units_saved': 0.0, 'co2e_saved': 0.0, 'revenue_generated': 0.0, 'waste_saved_kg': 0.0}
        user_id = default_customer.id
        print(f"✅ [Markov Estimator] Using customer ID: {user_id}")
    
    # Query inventory
    query = FruitInventory.query.filter(FruitInventory.quantity > 0)
    if store_id:
        query = query.filter(FruitInventory.store_id == store_id)
    
    inventory_items = query.all()
    print(f"🔍 [Markov Estimator] Found {len(inventory_items)} inventory items with quantity > 0")
    
    if len(inventory_items) == 0:
        print("⚠️ [Markov Estimator] No inventory items found")
        return {'units_saved': 0.0, 'co2e_saved': 0.0, 'revenue_generated': 0.0, 'waste_saved_kg': 0.0}
    
    total_units_saved = 0.0
    total_co2e_saved = 0.0
    total_revenue = 0.0
    total_waste_saved_kg = 0.0
    
    items_processed = 0
    items_with_units = 0
    
    for item in inventory_items:
        try:
            units = estimate_units_saved(
                item.id,
                baseline_params,
                dynamic_params,
                user_id
            )
            items_processed += 1
            
            if units > 0:
                items_with_units += 1
                co2e = estimate_co2e_saved(units, item.fruit_type)
                revenue = estimate_additional_revenue_generated(
                    units,
                    item.fruit_type,
                    item.current_price if item.current_price > 0 else item.original_price
                )
                
                # Convert units to weight (kg) for waste saved
                try:
                    from utils.waste_impact import calculate_weight_from_quantity
                    weight_kg = calculate_weight_from_quantity(item.fruit_type, units)
                except:
                    # Fallback: assume average 0.15 kg per unit
                    weight_kg = units * 0.15
                
                total_units_saved += units
                total_co2e_saved += co2e
                total_revenue += revenue
                total_waste_saved_kg += weight_kg
        except Exception as e:
            print(f"⚠️ [Markov Estimator] Error processing item {item.id} ({item.fruit_type}): {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"✅ [Markov Estimator] Processed {items_processed} items, {items_with_units} contributed to metrics")
    
    result = {
        'units_saved': round(total_units_saved, 2),
        'waste_saved_kg': round(total_waste_saved_kg, 2),
        'co2e_saved': round(total_co2e_saved, 2),
        'revenue_generated': round(total_revenue, 2)
    }
    
    print(f"📊 [Markov Estimator] Final metrics: {result}")
    
    return result

