"""
Knot API Integration
Handles communication with Knot API for customer transaction data
Documentation: https://docs.knotapi.com/
"""

import requests
from datetime import datetime, timedelta
import os
import base64


class KnotAPIClient:
    """Client for interacting with Knot API"""
    
    # Merchant IDs from Knot API
    MERCHANTS = {
        'amazon': 44,
        'costco': 165,
        'doordash': 19,
        'instacart': 40,
        'target': 12,
        'ubereats': 36,
        'walmart': 45
    }
    
    def __init__(self, client_id=None, secret=None):
        """
        Initialize Knot API client
        
        Args:
            client_id: Knot client ID (defaults to KNOT_CLIENT_ID env variable)
            secret: Knot secret (defaults to KNOT_SECRET env variable)
        """
        self.client_id = client_id or os.getenv('KNOT_CLIENT_ID', 'dda0778d-9486-47f8-bd80-6f2512f9bcdb')
        self.secret = secret or os.getenv('KNOT_SECRET', '884d84e855054c32a8e39d08fcd9845d')
        
        # Use development endpoint (for testing) or production
        self.base_url = os.getenv('KNOT_API_URL', 'https://development.knotapi.com')
        
        # Create Basic Auth header
        credentials = f"{self.client_id}:{self.secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        self.headers = {
            'Authorization': f'Basic {encoded}',
            'Content-Type': 'application/json'
        }
    
    def sync_transactions(self, external_user_id, merchant_ids=None, limit=100, cursor=None):
        """
        Sync transactions from Knot API
        
        Args:
            external_user_id: Your customer's ID in your system
            merchant_ids: List of merchant IDs to sync (defaults to grocery stores)
            limit: Maximum number of transactions to return (default 100)
            cursor: Pagination cursor for next page
            
        Returns:
            dict: Transaction data from Knot
        """
        # Default to grocery-related merchants if none specified
        if merchant_ids is None:
            merchant_ids = [
                self.MERCHANTS['instacart'],  # Instacart (most relevant for groceries)
                self.MERCHANTS['walmart'],    # Walmart
                self.MERCHANTS['target'],     # Target
                self.MERCHANTS['costco'],     # Costco
                self.MERCHANTS['amazon'],     # Amazon Fresh
            ]
        
        all_transactions = []
        
        # Sync from each merchant
        for merchant_id in merchant_ids:
            try:
                payload = {
                    'merchant_id': merchant_id,
                    'external_user_id': external_user_id,
                    'limit': limit
                }
                
                if cursor:
                    payload['cursor'] = cursor
                
                response = requests.post(
                    f'{self.base_url}/transactions/sync',
                    headers=self.headers,
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                transactions = data.get('transactions', [])
                all_transactions.extend(transactions)
                
                print(f"✅ Synced {len(transactions)} transactions from merchant {merchant_id}")
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Error syncing from merchant {merchant_id}: {e}")
                continue
        
        return {
            'transactions': all_transactions,
            'count': len(all_transactions),
            'external_user_id': external_user_id
        }
    
    def get_customer_transactions(self, external_user_id, limit=100):
        """
        Convenience method to get all grocery transactions for a customer
        
        Args:
            external_user_id: Your customer's ID
            limit: Max transactions per merchant
            
        Returns:
            list: All transactions
        """
        result = self.sync_transactions(external_user_id, limit=limit)
        return result.get('transactions', [])
    
    def sync_customer_data(self, external_user_id, customer_name=None, customer_email=None):
        """
        Sync customer order data from Knot to SusCart
        
        Args:
            external_user_id: Your customer's ID in your system
            customer_name: Customer's name (optional)
            customer_email: Customer's email (optional)
            
        Returns:
            dict: Synchronized customer data ready for SusCart
        """
        # Get orders from Knot (uses 'orders' not 'transactions')
        orders = self.get_customer_transactions(external_user_id, limit=100)
        
        if not orders:
            print(f"⚠️  No orders found for user {external_user_id}")
            return None
        
        # Analyze purchase patterns from orders
        preferences = self._analyze_purchase_patterns(orders)
        
        return {
            'external_user_id': external_user_id,
            'knot_customer_id': external_user_id,  # Use same ID for compatibility
            'name': customer_name or f'Customer {external_user_id}',
            'email': customer_email,
            'phone': None,
            'preferences': preferences,
            'orders': orders,
            'order_count': len(orders)
        }
    
    def _analyze_purchase_patterns(self, orders):
        """
        Analyze customer order history to determine preferences
        Matches the real Knot API format with 'products' not 'skus'
        
        Args:
            orders: List of order data from Knot API (real format)
            
        Returns:
            dict: Customer preferences
        """
        if not orders:
            return {
                'favorite_fruits': [],
                'favorite_products': [],
                'purchase_frequency': 0,
                'average_spend': 0,
                'preferred_discount': 0,
                'max_price': 10.0,
                'merchants_used': []
            }
        
        # Fruit keywords to identify produce
        fruit_keywords = [
            'apple', 'banana', 'orange', 'grape', 'strawberry', 'blueberry',
            'mango', 'pear', 'watermelon', 'peach', 'plum', 'cherry', 'kiwi',
            'pineapple', 'cantaloupe', 'honeydew', 'lemon', 'lime', 'grapefruit',
            'berry', 'fruit', 'produce', 'fresh', 'organic'
        ]
        
        fruit_counts = {}
        product_counts = {}
        total_spend = 0
        merchants = set()
        
        for order in orders:
            # Extract merchant from URL
            url = order.get('url', '')
            if 'instacart' in url:
                merchants.add('Instacart')
            elif 'walmart' in url:
                merchants.add('Walmart')
            elif 'target' in url:
                merchants.add('Target')
            elif 'costco' in url:
                merchants.add('Costco')
            elif 'amazon' in url:
                merchants.add('Amazon')
            elif 'doordash' in url:
                merchants.add('Doordash')
            elif 'ubereats' in url:
                merchants.add('Ubereats')
            
            # Get order total
            price = order.get('price', {})
            total = price.get('total', 0)
            total_spend += abs(total)
            
            # Analyze products (not skus!)
            products = order.get('products', [])
            
            for product in products:
                product_name = product.get('name', '').lower()
                
                # Track product
                if product_name:
                    product_counts[product_name] = product_counts.get(product_name, 0) + product.get('quantity', 1)
                
                # Check if it's a fruit
                for keyword in fruit_keywords:
                    if keyword in product_name:
                        fruit_counts[keyword] = fruit_counts.get(keyword, 0) + product.get('quantity', 1)
        
        # Get top 5 favorite fruits
        sorted_fruits = sorted(fruit_counts.items(), key=lambda x: x[1], reverse=True)
        favorite_fruits = [fruit for fruit, _ in sorted_fruits[:5]]
        
        # Get top 5 products
        sorted_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)
        favorite_products = [product for product, _ in sorted_products[:5]]
        
        # Calculate averages
        num_orders = len(orders)
        average_spend = total_spend / num_orders if num_orders > 0 else 0
        
        return {
            'favorite_fruits': favorite_fruits,
            'favorite_products': favorite_products,
            'purchase_frequency': num_orders / 90,  # orders per day (assume 90 day window)
            'average_spend': round(average_spend, 2),
            'preferred_discount': 20,  # Default to 20%
            'max_price': round(average_spend * 2, 2),  # willing to pay 2x average
            'merchants_used': list(merchants),
            'total_orders': num_orders
        }
    
    def webhook_handler(self, webhook_data):
        """
        Handle incoming webhooks from Knot
        
        Args:
            webhook_data: Webhook payload from Knot
            
        Returns:
            dict: Processed webhook data
        """
        event_type = webhook_data.get('event_type')
        
        if event_type == 'purchase.created':
            return {
                'type': 'new_purchase',
                'customer_id': webhook_data.get('customer_id'),
                'transaction_id': webhook_data.get('transaction_id'),
                'items': webhook_data.get('items', []),
                'timestamp': webhook_data.get('timestamp')
            }
        elif event_type == 'customer.updated':
            return {
                'type': 'customer_updated',
                'customer_id': webhook_data.get('customer_id'),
                'changes': webhook_data.get('changes', {})
            }
        
        return None


# Mock Knot API for testing (when API key not available)
class MockKnotAPIClient(KnotAPIClient):
    """Mock client for testing without real Knot API access"""
    
    def __init__(self):
        # Don't call parent __init__ to avoid needing API key
        self.base_url = 'mock://knot-api'
        self.mock_data = self._generate_mock_data()
    
    def _generate_mock_data(self):
        """Generate mock order data matching real Knot API format"""
        return {
            'user123': {
                'orders': [
                    {
                        'externalId': '029f1e08-9015-4118-a698-ddf6b296eda3',
                        'dateTime': (datetime.utcnow() - timedelta(days=3)).isoformat(),
                        'url': 'https://www.instacart.com/store/orders/029f1e08-9015-4118-a698-ddf6b296eda3',
                        'orderStatus': 'DELIVERED',
                        'price': {
                            'subTotal': 45.67,
                            'total': 50.23,
                            'currency': 'USD'
                        },
                        'products': [
                            {
                                'externalId': '1200354',
                                'name': 'Organic Bananas - 2 lbs',
                                'url': 'https://www.instacart.com/product/1200354',
                                'quantity': 2,
                                'price': {
                                    'subTotal': 5.98,
                                    'total': 5.98,
                                    'unitPrice': 2.99,
                                    'currency': 'USD'
                                }
                            },
                            {
                                'externalId': '1200355',
                                'name': 'Honeycrisp Apples - 3 lb bag',
                                'url': 'https://www.instacart.com/product/1200355',
                                'quantity': 1,
                                'price': {
                                    'subTotal': 8.99,
                                    'total': 8.99,
                                    'unitPrice': 8.99,
                                    'currency': 'USD'
                                }
                            },
                            {
                                'externalId': '1200356',
                                'name': 'Fresh Strawberries - 1 lb',
                                'url': 'https://www.instacart.com/product/1200356',
                                'quantity': 3,
                                'price': {
                                    'subTotal': 17.97,
                                    'total': 17.97,
                                    'unitPrice': 5.99,
                                    'currency': 'USD'
                                }
                            },
                            {
                                'externalId': '1200357',
                                'name': 'Organic Blueberries - 6 oz',
                                'url': 'https://www.instacart.com/product/1200357',
                                'quantity': 2,
                                'price': {
                                    'subTotal': 11.98,
                                    'total': 11.98,
                                    'unitPrice': 5.99,
                                    'currency': 'USD'
                                }
                            }
                        ]
                    },
                    {
                        'externalId': '4151632',
                        'dateTime': (datetime.utcnow() - timedelta(days=7)).isoformat(),
                        'url': 'https://www.walmart.com/orders/4151632',
                        'orderStatus': 'DELIVERED',
                        'price': {
                            'subTotal': 32.45,
                            'total': 35.12,
                            'currency': 'USD'
                        },
                        'products': [
                            {
                                'externalId': '808080808',
                                'name': 'Navel Oranges - 3 lb bag',
                                'url': 'https://www.walmart.com/ip/808080808',
                                'quantity': 1,
                                'price': {
                                    'subTotal': 7.99,
                                    'total': 7.99,
                                    'unitPrice': 7.99,
                                    'currency': 'USD'
                                }
                            },
                            {
                                'externalId': '808080809',
                                'name': 'Red Seedless Grapes - 2 lbs',
                                'url': 'https://www.walmart.com/ip/808080809',
                                'quantity': 2,
                                'price': {
                                    'subTotal': 10.98,
                                    'total': 10.98,
                                    'unitPrice': 5.49,
                                    'currency': 'USD'
                                }
                            },
                            {
                                'externalId': '808080810',
                                'name': 'Fresh Mango',
                                'url': 'https://www.walmart.com/ip/808080810',
                                'quantity': 3,
                                'price': {
                                    'subTotal': 8.97,
                                    'total': 8.97,
                                    'unitPrice': 2.99,
                                    'currency': 'USD'
                                }
                            }
                        ]
                    },
                    {
                        'externalId': '09f3cdc2-2443-4f64-ade7-5f897f25768e',
                        'dateTime': (datetime.utcnow() - timedelta(days=14)).isoformat(),
                        'url': 'www.costco.com/order/09f3cdc2-2443-4f64-ade7-5f897f25768e',
                        'orderStatus': 'SHIPPED',
                        'price': {
                            'subTotal': 28.96,
                            'total': 31.92,
                            'currency': 'USD'
                        },
                        'products': [
                            {
                                'externalId': '1200200857',
                                'name': 'Kirkland Signature Organic Blueberries, 4 lb',
                                'url': 'https://www.costco.com/product/1200200857',
                                'quantity': 1,
                                'price': {
                                    'subTotal': 10.99,
                                    'total': 10.99,
                                    'unitPrice': 10.99,
                                    'currency': 'USD'
                                }
                            },
                            {
                                'externalId': '1200200858',
                                'name': 'Gala Apples - 5 lb bag',
                                'url': 'https://www.costco.com/product/1200200858',
                                'quantity': 1,
                                'price': {
                                    'subTotal': 7.49,
                                    'total': 7.49,
                                    'unitPrice': 7.49,
                                    'currency': 'USD'
                                }
                            },
                            {
                                'externalId': '1200200859',
                                'name': 'Organic Bananas - 3 lbs',
                                'url': 'https://www.costco.com/product/1200200859',
                                'quantity': 2,
                                'price': {
                                    'subTotal': 7.98,
                                    'total': 7.98,
                                    'unitPrice': 3.99,
                                    'currency': 'USD'
                                }
                            }
                        ]
                    }
                ]
            },
            'user456': {
                'orders': [
                    {
                        'externalId': 'fac1f902-1308-42e1-b93a-5b9bebd887ef',
                        'dateTime': (datetime.utcnow() - timedelta(days=2)).isoformat(),
                        'url': 'https://orders.target.com/order/fac1f902-1308-42e1-b93a-5b9bebd887ef',
                        'orderStatus': 'DELIVERED',
                        'price': {
                            'subTotal': 22.45,
                            'total': 24.12,
                            'currency': 'USD'
                        },
                        'products': [
                            {
                                'externalId': '1200262',
                                'name': 'Watermelon - Seedless',
                                'url': 'https://www.target.com/product/1200262',
                                'quantity': 1,
                                'price': {
                                    'subTotal': 8.99,
                                    'total': 8.99,
                                    'unitPrice': 8.99,
                                    'currency': 'USD'
                                }
                            },
                            {
                                'externalId': '1200263',
                                'name': 'Fresh Pineapple',
                                'url': 'https://www.target.com/product/1200263',
                                'quantity': 2,
                                'price': {
                                    'subTotal': 11.98,
                                    'total': 11.98,
                                    'unitPrice': 5.99,
                                    'currency': 'USD'
                                }
                            }
                        ]
                    }
                ]
            }
        }
    
    def sync_transactions(self, external_user_id, merchant_ids=None, limit=100, cursor=None):
        """Return mock order data"""
        data = self.mock_data.get(external_user_id)
        if not data:
            return {'orders': [], 'count': 0, 'external_user_id': external_user_id}
        
        orders = data.get('orders', [])
        return {
            'orders': orders[:limit],
            'count': len(orders),
            'external_user_id': external_user_id
        }
    
    def get_customer_transactions(self, external_user_id, limit=100):
        """Return mock orders"""
        result = self.sync_transactions(external_user_id, limit=limit)
        return result.get('orders', [])


def get_knot_client():
    """
    Factory function to get appropriate Knot API client
    Uses real client if credentials are configured, otherwise returns mock client
    """
    # Check if custom credentials are provided
    client_id = os.getenv('KNOT_CLIENT_ID')
    secret = os.getenv('KNOT_SECRET')
    use_real = os.getenv('KNOT_USE_REAL', 'false').lower() == 'true'
    
    # If KNOT_USE_REAL is explicitly set to true, use real API with provided/default credentials
    if use_real:
        print("🔗 Using REAL Knot API client")
        print(f"   Client ID: {client_id[:20] if client_id else 'dda0778d-9486-47f8'}...")
        print(f"   Base URL: {os.getenv('KNOT_API_URL', 'https://development.knotapi.com')}")
        return KnotAPIClient(client_id, secret)
    else:
        print("🔗 Using MOCK Knot API client")
        print("   Set KNOT_USE_REAL=true in .env to use real Knot API")
        return MockKnotAPIClient()

