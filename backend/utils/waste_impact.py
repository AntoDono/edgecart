"""
Waste Impact Calculation Module
Calculates food waste reduction and CO2 emissions saved
Based on scientific data and industry standards
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func
from models import db, FruitInventory, FreshnessStatus, PurchaseHistory, WasteLog, Recommendation

# CO2 Emission Factors (kg CO2 per kg of food waste)
# Source: EPA, FAO, and academic research
# These represent the full lifecycle emissions (production, transport, disposal)
CO2_EMISSION_FACTORS = {
    'apple': 0.43,      # kg CO2 per kg
    'banana': 0.48,
    'orange': 0.39,
    'strawberry': 0.67,  # Higher due to refrigeration needs
    'grape': 0.46,
    'avocado': 0.85,    # High due to water-intensive production
    'tomato': 0.25,
    'lettuce': 0.35,
    'blueberry': 0.72,
    'mango': 0.55,
    'pear': 0.40,
    'watermelon': 0.30,
    'peach': 0.38,
    'cherry': 0.65,
    # Default for unknown fruits
    'default': 0.45
}

# Average weight per unit (kg) - used to convert quantity to weight
AVERAGE_WEIGHT_PER_UNIT = {
    'apple': 0.18,      # ~180g per apple
    'banana': 0.12,     # ~120g per banana
    'orange': 0.15,
    'strawberry': 0.02, # ~20g per strawberry (50 per lb)
    'grape': 0.005,     # ~5g per grape
    'avocado': 0.20,
    'tomato': 0.15,
    'lettuce': 0.30,    # per head
    'blueberry': 0.001, # ~1g per blueberry
    'mango': 0.35,
    'pear': 0.18,
    'watermelon': 4.5,  # per watermelon
    'peach': 0.15,
    'cherry': 0.008,
    'default': 0.15
}

# Industry baseline waste rates (percentage of inventory that goes to waste)
# Source: ReFED, USDA, industry reports
BASELINE_WASTE_RATES = {
    'apple': 0.12,      # 12% waste rate without intervention
    'banana': 0.15,     # 15% - bananas spoil quickly
    'orange': 0.10,
    'strawberry': 0.20, # 20% - very perishable
    'grape': 0.18,
    'avocado': 0.25,    # 25% - high waste rate
    'tomato': 0.15,
    'lettuce': 0.22,
    'blueberry': 0.18,
    'mango': 0.20,
    'pear': 0.12,
    'watermelon': 0.15,
    'peach': 0.18,
    'cherry': 0.20,
    'default': 0.15     # 15% average for produce
}

# Discount effectiveness rates
# Based on research: higher discounts = higher purchase probability
DISCOUNT_EFFECTIVENESS = {
    0: 0.0,      # No discount = no additional sales
    10: 0.15,    # 10% discount = 15% chance of preventing waste
    25: 0.45,    # 25% discount = 45% chance
    50: 0.75,    # 50% discount = 75% chance
    75: 0.90     # 75% discount = 90% chance
}


def get_emission_factor(fruit_type: str) -> float:
    """Get CO2 emission factor for a fruit type"""
    return CO2_EMISSION_FACTORS.get(fruit_type.lower(), CO2_EMISSION_FACTORS['default'])


def get_average_weight(fruit_type: str) -> float:
    """Get average weight per unit for a fruit type"""
    return AVERAGE_WEIGHT_PER_UNIT.get(fruit_type.lower(), AVERAGE_WEIGHT_PER_UNIT['default'])


def get_baseline_waste_rate(fruit_type: str) -> float:
    """Get baseline waste rate for a fruit type"""
    return BASELINE_WASTE_RATES.get(fruit_type.lower(), BASELINE_WASTE_RATES['default'])


def calculate_weight_from_quantity(fruit_type: str, quantity: int) -> float:
    """Convert quantity (units) to weight (kg)"""
    return quantity * get_average_weight(fruit_type)


def calculate_co2_saved(fruit_type: str, weight_kg: float) -> float:
    """Calculate CO2 emissions saved by preventing waste (kg CO2)"""
    emission_factor = get_emission_factor(fruit_type)
    return weight_kg * emission_factor


def calculate_waste_prevented_by_discount(
    inventory_id: int,
    discount_percentage: float,
    quantity_sold: int
) -> Tuple[float, float]:
    """
    Calculate waste prevented and CO2 saved from a discounted sale
    
    Returns:
        (waste_prevented_kg, co2_saved_kg)
    """
    item = FruitInventory.query.get(inventory_id)
    if not item:
        return (0.0, 0.0)
    
    fruit_type = item.fruit_type
    
    # Calculate weight of items sold
    weight_sold_kg = calculate_weight_from_quantity(fruit_type, quantity_sold)
    
    # Estimate effectiveness based on discount level
    # Interpolate discount effectiveness
    discount_effectiveness = _interpolate_discount_effectiveness(discount_percentage)
    
    # Waste prevented = weight sold * effectiveness
    # (Not all discounted sales would have been waste, but we estimate based on discount level)
    waste_prevented_kg = weight_sold_kg * discount_effectiveness
    
    # CO2 saved
    co2_saved_kg = calculate_co2_saved(fruit_type, waste_prevented_kg)
    
    return (waste_prevented_kg, co2_saved_kg)


def _interpolate_discount_effectiveness(discount: float) -> float:
    """Interpolate discount effectiveness for any discount percentage"""
    discounts = sorted(DISCOUNT_EFFECTIVENESS.keys())
    
    if discount <= discounts[0]:
        return DISCOUNT_EFFECTIVENESS[discounts[0]]
    if discount >= discounts[-1]:
        return DISCOUNT_EFFECTIVENESS[discounts[-1]]
    
    # Find the two closest discount levels
    for i in range(len(discounts) - 1):
        if discounts[i] <= discount <= discounts[i + 1]:
            # Linear interpolation
            low_disc = discounts[i]
            high_disc = discounts[i + 1]
            low_eff = DISCOUNT_EFFECTIVENESS[low_disc]
            high_eff = DISCOUNT_EFFECTIVENESS[high_disc]
            
            ratio = (discount - low_disc) / (high_disc - low_disc)
            return low_eff + (high_eff - low_eff) * ratio
    
    return 0.5  # Default


def calculate_baseline_waste(
    fruit_type: str,
    total_quantity: int,
    days_in_store: int
) -> float:
    """
    Calculate expected waste without the system (baseline)
    
    Uses baseline waste rate adjusted for time in store
    """
    baseline_rate = get_baseline_waste_rate(fruit_type)
    
    # Adjust for time - longer in store = higher waste probability
    # Simple linear adjustment: +1% per day after 3 days
    time_adjustment = max(0, (days_in_store - 3) * 0.01)
    adjusted_rate = min(1.0, baseline_rate + time_adjustment)
    
    total_weight_kg = calculate_weight_from_quantity(fruit_type, total_quantity)
    expected_waste_kg = total_weight_kg * adjusted_rate
    
    return expected_waste_kg


def calculate_actual_waste_with_system(
    inventory_id: int,
    quantity_wasted: int
) -> Tuple[float, float]:
    """
    Calculate actual waste that occurred with the system
    Returns: (waste_kg, co2_emitted_kg)
    """
    item = FruitInventory.query.get(inventory_id)
    if not item:
        return (0.0, 0.0)
    
    fruit_type = item.fruit_type
    waste_kg = calculate_weight_from_quantity(fruit_type, quantity_wasted)
    co2_emitted_kg = calculate_co2_saved(fruit_type, waste_kg)  # Same calculation
    
    return (waste_kg, co2_emitted_kg)


def calculate_impact_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    store_id: Optional[int] = None
) -> Dict:
    """
    Calculate comprehensive impact metrics
    
    Returns:
    {
        'waste_prevented_kg': float,
        'co2_saved_kg': float,
        'baseline_waste_kg': float,
        'actual_waste_kg': float,
        'waste_reduction_percentage': float,
        'revenue_recovered': float,
        'items_saved': int,
        'recommendations_sent': int,
        'recommendations_purchased': int,
        'conversion_rate': float
    }
    """
    # Set default date range (last 30 days)
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # Build query filters
    query = PurchaseHistory.query.filter(
        PurchaseHistory.purchase_date >= start_date,
        PurchaseHistory.purchase_date <= end_date
    )
    
    if store_id:
        query = query.join(FruitInventory).filter(FruitInventory.store_id == store_id)
    
    # Get all purchases with discounts
    purchases = query.join(FruitInventory).join(FreshnessStatus).filter(
        FreshnessStatus.discount_percentage > 0
    ).all()
    
    # Calculate waste prevented from discounted sales
    total_waste_prevented_kg = 0.0
    total_co2_saved_kg = 0.0
    total_revenue_recovered = 0.0
    items_saved = 0
    
    for purchase in purchases:
        item = purchase.inventory
        freshness = item.freshness
        
        if freshness and freshness.discount_percentage > 0:
            waste_kg, co2_kg = calculate_waste_prevented_by_discount(
                item.id,
                freshness.discount_percentage,
                purchase.quantity
            )
            
            total_waste_prevented_kg += waste_kg
            total_co2_saved_kg += co2_kg
            total_revenue_recovered += purchase.price_paid
            items_saved += purchase.quantity
    
    # Calculate baseline waste (what would have happened without system)
    inventory_query = FruitInventory.query.filter(
        FruitInventory.created_at >= start_date,
        FruitInventory.created_at <= end_date
    )
    
    if store_id:
        inventory_query = inventory_query.filter(FruitInventory.store_id == store_id)
    
    all_items = inventory_query.all()
    
    total_baseline_waste_kg = 0.0
    for item in all_items:
        days_in_store = (end_date - item.arrival_date).days if item.arrival_date else 0
        baseline_waste = calculate_baseline_waste(
            item.fruit_type,
            item.quantity + sum(p.quantity for p in item.purchases),  # Original quantity
            days_in_store
        )
        total_baseline_waste_kg += baseline_waste
    
    # Calculate actual waste that occurred
    waste_logs_query = WasteLog.query.filter(
        WasteLog.logged_at >= start_date,
        WasteLog.logged_at <= end_date
    )
    
    if store_id:
        waste_logs_query = waste_logs_query.join(FruitInventory).filter(
            FruitInventory.store_id == store_id
        )
    
    waste_logs = waste_logs_query.all()
    
    total_actual_waste_kg = 0.0
    total_co2_emitted_kg = 0.0
    
    for waste_log in waste_logs:
        waste_kg, co2_kg = calculate_actual_waste_with_system(
            waste_log.inventory_id,
            waste_log.quantity_wasted
        )
        total_actual_waste_kg += waste_kg
        total_co2_emitted_kg += co2_kg
    
    # Calculate waste reduction percentage
    if total_baseline_waste_kg > 0:
        waste_reduction_pct = ((total_baseline_waste_kg - total_actual_waste_kg) / total_baseline_waste_kg) * 100
    else:
        waste_reduction_pct = 0.0
    
    # Recommendation metrics
    rec_query = Recommendation.query.filter(
        Recommendation.sent_at >= start_date,
        Recommendation.sent_at <= end_date
    )
    
    if store_id:
        rec_query = rec_query.join(FruitInventory).filter(FruitInventory.store_id == store_id)
    
    recommendations = rec_query.all()
    recommendations_sent = len(recommendations)
    recommendations_purchased = sum(1 for r in recommendations if r.purchased)
    
    conversion_rate = (recommendations_purchased / recommendations_sent * 100) if recommendations_sent > 0 else 0.0
    
    return {
        'waste_prevented_kg': round(total_waste_prevented_kg, 2),
        'co2_saved_kg': round(total_co2_saved_kg, 2),
        'baseline_waste_kg': round(total_baseline_waste_kg, 2),
        'actual_waste_kg': round(total_actual_waste_kg, 2),
        'waste_reduction_percentage': round(waste_reduction_pct, 1),
        'revenue_recovered': round(total_revenue_recovered, 2),
        'items_saved': items_saved,
        'recommendations_sent': recommendations_sent,
        'recommendations_purchased': recommendations_purchased,
        'conversion_rate': round(conversion_rate, 1),
        'co2_emitted_kg': round(total_co2_emitted_kg, 2),
        'net_co2_saved_kg': round(total_co2_saved_kg - total_co2_emitted_kg, 2),
        'period_start': start_date.isoformat(),
        'period_end': end_date.isoformat()
    }


def simulate_impact_for_item(
    inventory_id: int,
    discount_percentage: float,
    days_until_expiry: int
) -> Dict:
    """
    Simulate potential impact if item is discounted
    
    Used for predictive analytics - shows "what if" scenarios
    """
    item = FruitInventory.query.get(inventory_id)
    if not item:
        return {}
    
    fruit_type = item.fruit_type
    quantity = item.quantity
    
    # Estimate sales probability based on discount and time
    discount_effectiveness = _interpolate_discount_effectiveness(discount_percentage)
    
    # Time urgency factor (closer to expiry = higher urgency = more likely to sell)
    urgency_factor = max(0.3, 1.0 - (days_until_expiry / 10.0))
    sales_probability = discount_effectiveness * urgency_factor
    
    # Estimate quantity that would sell
    estimated_sales = int(quantity * sales_probability)
    
    # Calculate impact
    weight_kg = calculate_weight_from_quantity(fruit_type, estimated_sales)
    waste_prevented_kg = weight_kg * discount_effectiveness
    co2_saved_kg = calculate_co2_saved(fruit_type, waste_prevented_kg)
    revenue_recovered = item.current_price * estimated_sales
    
    # Baseline comparison
    days_in_store = (datetime.utcnow() - item.arrival_date).days if item.arrival_date else 0
    baseline_waste_kg = calculate_baseline_waste(fruit_type, quantity, days_in_store)
    
    return {
        'inventory_id': inventory_id,
        'fruit_type': fruit_type,
        'current_quantity': quantity,
        'estimated_sales': estimated_sales,
        'sales_probability': round(sales_probability * 100, 1),
        'waste_prevented_kg': round(waste_prevented_kg, 2),
        'co2_saved_kg': round(co2_saved_kg, 2),
        'revenue_recovered': round(revenue_recovered, 2),
        'baseline_waste_kg': round(baseline_waste_kg, 2),
        'potential_reduction_pct': round((waste_prevented_kg / baseline_waste_kg * 100) if baseline_waste_kg > 0 else 0, 1)
    }


def get_time_series_impact(
    days: int = 30,
    store_id: Optional[int] = None
) -> List[Dict]:
    """
    Get daily impact metrics for time series visualization
    
    Returns list of daily metrics
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    daily_metrics = []
    
    for day_offset in range(days):
        day_start = start_date + timedelta(days=day_offset)
        day_end = day_start + timedelta(days=1)
        
        metrics = calculate_impact_metrics(day_start, day_end, store_id)
        metrics['date'] = day_start.date().isoformat()
        daily_metrics.append(metrics)
    
    return daily_metrics

