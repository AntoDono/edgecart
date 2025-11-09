"""
Seed initial data for Markov waste estimator models
Run this after database initialization to populate price curves and product LCA data
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, PriceCurve, ProductLCA
from database import init_db
from flask import Flask


def seed_markov_data(app):
    """Seed price curves and product LCA data"""
    with app.app_context():
        # Check if data already exists
        if PriceCurve.query.first():
            print("⚠️  Price curves already exist. Skipping seed.")
        else:
            print("📊 Seeding price curves...")
            
            # Default price-response curves based on research
            # Format: [discount_bins], [buy_probabilities]
            # These are conservative estimates based on industry research
            price_curves = [
                {
                    'category': 'apple',
                    'x_discount_bins': [0, 10, 25, 50, 75],
                    'y_pbuy': [0.05, 0.15, 0.45, 0.75, 0.90]
                },
                {
                    'category': 'banana',
                    'x_discount_bins': [0, 10, 25, 50, 75],
                    'y_pbuy': [0.05, 0.18, 0.50, 0.78, 0.92]
                },
                {
                    'category': 'orange',
                    'x_discount_bins': [0, 10, 25, 50, 75],
                    'y_pbuy': [0.05, 0.15, 0.45, 0.75, 0.90]
                },
                {
                    'category': 'strawberry',
                    'x_discount_bins': [0, 10, 25, 50, 75],
                    'y_pbuy': [0.05, 0.20, 0.55, 0.80, 0.95]  # More price-sensitive
                },
                {
                    'category': 'grape',
                    'x_discount_bins': [0, 10, 25, 50, 75],
                    'y_pbuy': [0.05, 0.15, 0.45, 0.75, 0.90]
                },
                {
                    'category': 'avocado',
                    'x_discount_bins': [0, 10, 25, 50, 75],
                    'y_pbuy': [0.05, 0.25, 0.60, 0.85, 0.95]  # Very price-sensitive
                },
                {
                    'category': 'tomato',
                    'x_discount_bins': [0, 10, 25, 50, 75],
                    'y_pbuy': [0.05, 0.15, 0.45, 0.75, 0.90]
                },
                {
                    'category': 'lettuce',
                    'x_discount_bins': [0, 10, 25, 50, 75],
                    'y_pbuy': [0.05, 0.20, 0.50, 0.78, 0.92]
                },
                {
                    'category': 'blueberry',
                    'x_discount_bins': [0, 10, 25, 50, 75],
                    'y_pbuy': [0.05, 0.18, 0.48, 0.76, 0.91]
                },
                {
                    'category': 'mango',
                    'x_discount_bins': [0, 10, 25, 50, 75],
                    'y_pbuy': [0.05, 0.22, 0.55, 0.80, 0.93]
                }
            ]
            
            for curve_data in price_curves:
                curve = PriceCurve(
                    category=curve_data['category'],
                    x_discount_bins=curve_data['x_discount_bins'],
                    y_pbuy=curve_data['y_pbuy']
                )
                db.session.add(curve)
            
            db.session.commit()
            print(f"✅ Created {len(price_curves)} price curves")
        
        # Seed Product LCA data
        if ProductLCA.query.first():
            print("⚠️  Product LCA data already exists. Skipping seed.")
        else:
            print("🌍 Seeding product LCA data...")
            
            # LCA data based on research (EPA, FAO, academic studies)
            # mass_kg: average weight per unit
            # ef_prod_kgco2e_perkg: production emission factor
            # ef_disposal_kgco2e_perunit: disposal emission factor
            # displacement: displacement factor (0-1, typically 1.0 for full displacement)
            product_lca_data = [
                {
                    'product_name': 'apple',
                    'mass_kg': 0.18,
                    'ef_prod_kgco2e_perkg': 0.43,
                    'ef_disposal_kgco2e_perunit': 0.08,
                    'displacement': 1.0
                },
                {
                    'product_name': 'banana',
                    'mass_kg': 0.12,
                    'ef_prod_kgco2e_perkg': 0.48,
                    'ef_disposal_kgco2e_perunit': 0.06,
                    'displacement': 1.0
                },
                {
                    'product_name': 'orange',
                    'mass_kg': 0.15,
                    'ef_prod_kgco2e_perkg': 0.39,
                    'ef_disposal_kgco2e_perunit': 0.06,
                    'displacement': 1.0
                },
                {
                    'product_name': 'strawberry',
                    'mass_kg': 0.02,
                    'ef_prod_kgco2e_perkg': 0.67,
                    'ef_disposal_kgco2e_perunit': 0.01,
                    'displacement': 1.0
                },
                {
                    'product_name': 'grape',
                    'mass_kg': 0.005,
                    'ef_prod_kgco2e_perkg': 0.46,
                    'ef_disposal_kgco2e_perunit': 0.002,
                    'displacement': 1.0
                },
                {
                    'product_name': 'avocado',
                    'mass_kg': 0.20,
                    'ef_prod_kgco2e_perkg': 0.85,
                    'ef_disposal_kgco2e_perunit': 0.17,
                    'displacement': 1.0
                },
                {
                    'product_name': 'tomato',
                    'mass_kg': 0.15,
                    'ef_prod_kgco2e_perkg': 0.25,
                    'ef_disposal_kgco2e_perunit': 0.04,
                    'displacement': 1.0
                },
                {
                    'product_name': 'lettuce',
                    'mass_kg': 0.30,
                    'ef_prod_kgco2e_perkg': 0.35,
                    'ef_disposal_kgco2e_perunit': 0.11,
                    'displacement': 1.0
                },
                {
                    'product_name': 'blueberry',
                    'mass_kg': 0.001,
                    'ef_prod_kgco2e_perkg': 0.72,
                    'ef_disposal_kgco2e_perunit': 0.001,
                    'displacement': 1.0
                },
                {
                    'product_name': 'mango',
                    'mass_kg': 0.35,
                    'ef_prod_kgco2e_perkg': 0.55,
                    'ef_disposal_kgco2e_perunit': 0.19,
                    'displacement': 1.0
                }
            ]
            
            for lca_data in product_lca_data:
                lca = ProductLCA(**lca_data)
                db.session.add(lca)
            
            db.session.commit()
            print(f"✅ Created {len(product_lca_data)} product LCA records")
        
        print("✅ Markov estimator data seeding complete!")


if __name__ == "__main__":
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///instance/suscart_prod.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    init_db(app)
    seed_markov_data(app)

