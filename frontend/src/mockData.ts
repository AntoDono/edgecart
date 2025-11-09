// Mock data for demo profiles when backend is unavailable
export const mockCustomers = {
  'abc': {
    id: 1,
    knot_customer_id: 'abc',
    name: 'Sarah Chen',
    email: 'sarah@example.com',
    preferences: {
      favorite_fruits: ['Banana', 'Apple', 'Orange'],
      favorite_products: ['Organic Berries', 'Fresh Greens'],
      average_spend: 45.50,
      merchants_used: ['Whole Foods', 'Trader Joe\'s'],
      total_transactions: 24,
      max_price: 100,
      preferred_discount: 15
    }
  },
  'def': {
    id: 2,
    knot_customer_id: 'def',
    name: 'Marcus Lee',
    email: 'marcus@example.com',
    preferences: {
      favorite_fruits: ['Banana', 'Apple', 'Orange'],
      favorite_products: ['Citrus Fruits', 'Leafy Greens'],
      average_spend: 52.30,
      merchants_used: ['Whole Foods', 'Sprouts'],
      total_transactions: 31,
      max_price: 120,
      preferred_discount: 20
    }
  },
  'ghi': {
    id: 3,
    knot_customer_id: 'ghi',
    name: 'Emily Rodriguez',
    email: 'emily@example.com',
    preferences: {
      favorite_fruits: ['Banana', 'Apple', 'Orange', 'Pear'],
      favorite_products: ['Exotic Fruits', 'Organic Produce'],
      average_spend: 68.90,
      merchants_used: ['Whole Foods', 'Asian Market', 'Farmers Market'],
      total_transactions: 42,
      max_price: 150,
      preferred_discount: 25
    }
  }
};

export const mockRecommendations = {
  'abc': [
<<<<<<< HEAD
    // No hardcoded recommendations - will be fetched from backend
=======
    {
      id: 1,
      inventory_id: 101,
      priority_score: 95,
      sent_at: new Date().toISOString(),
      viewed: false,
      purchased: false,
      item: {
        id: 101,
        fruit_type: 'Banana',
        variety: 'Organic',
        quantity: 15,
        original_price: 3.99,
        current_price: 2.49,
        discount_percentage: 38,
        freshness: {
          freshness_score: 85,
          status: 'fresh',
          predicted_expiry_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString()
        }
      },
      reason: {
        match_type: 'favorite_fruit',
        fruit: 'Banana',
        reasoning: 'Fresh organic bananas just arrived! Perfect for your breakfast routine.',
        discount: 38
      }
    },
    {
      id: 2,
      inventory_id: 102,
      priority_score: 88,
      sent_at: new Date().toISOString(),
      viewed: false,
      purchased: false,
      item: {
        id: 102,
        fruit_type: 'Apple',
        variety: 'Honeycrisp',
        quantity: 20,
        original_price: 5.99,
        current_price: 3.99,
        discount_percentage: 33,
        freshness: {
          freshness_score: 92,
          status: 'fresh',
          predicted_expiry_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
        }
      },
      reason: {
        match_type: 'favorite_fruit',
        fruit: 'Apple',
        reasoning: 'Crisp honeycrisp apples on sale - sweet and refreshing!',
        discount: 33
      }
    }
>>>>>>> 5067a06457a029600a19d2a6f6b1afae288b8f4c
  ],
  'def': [
    {
      id: 3,
      inventory_id: 201,
      priority_score: 92,
      sent_at: new Date().toISOString(),
      viewed: false,
      purchased: false,
      item: {
        id: 201,
        fruit_type: 'Orange',
        variety: 'Valencia',
        quantity: 30,
        original_price: 5.99,
        current_price: 3.99,
        discount_percentage: 33,
        freshness: {
          freshness_score: 90,
          status: 'fresh',
          predicted_expiry_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString()
        }
      },
      reason: {
        match_type: 'favorite_fruit',
        fruit: 'Orange',
        reasoning: 'Sweet Valencia oranges perfect for your fitness routine!',
        discount: 33
      }
    },
    {
      id: 4,
      inventory_id: 202,
      priority_score: 87,
      sent_at: new Date().toISOString(),
      viewed: false,
      purchased: false,
      item: {
        id: 202,
        fruit_type: 'Banana',
        variety: 'Organic',
        quantity: 18,
        original_price: 3.99,
        current_price: 2.49,
        discount_percentage: 38,
        freshness: {
          freshness_score: 88,
          status: 'fresh',
          predicted_expiry_date: new Date(Date.now() + 4 * 24 * 60 * 60 * 1000).toISOString()
        }
      },
      reason: {
        match_type: 'favorite_fruit',
        fruit: 'Banana',
        reasoning: 'Organic bananas on sale - perfect for your smoothies!',
        discount: 38
      }
    }
  ],
  'ghi': [
    {
      id: 5,
      inventory_id: 301,
      priority_score: 96,
      sent_at: new Date().toISOString(),
      viewed: false,
      purchased: false,
      item: {
        id: 301,
        fruit_type: 'Pear',
        variety: 'Bartlett',
        quantity: 12,
        original_price: 4.99,
        current_price: 2.99,
        discount_percentage: 40,
        freshness: {
          freshness_score: 88,
          status: 'fresh',
          predicted_expiry_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString()
        }
      },
      reason: {
        match_type: 'favorite_fruit',
        fruit: 'Pear',
        reasoning: 'Fresh Bartlett pears just for you - sweet and juicy!',
        discount: 40
      }
    },
    {
      id: 6,
      inventory_id: 302,
      priority_score: 90,
      sent_at: new Date().toISOString(),
      viewed: false,
      purchased: false,
      item: {
        id: 302,
        fruit_type: 'Apple',
        variety: 'Gala',
        quantity: 25,
        original_price: 5.49,
        current_price: 3.49,
        discount_percentage: 36,
        freshness: {
          freshness_score: 90,
          status: 'fresh',
          predicted_expiry_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
        }
      },
      reason: {
        match_type: 'favorite_fruit',
        fruit: 'Apple',
        reasoning: 'Sweet and crisp Gala apples - perfect for snacking!',
        discount: 36
      }
    },
    {
      id: 7,
      inventory_id: 303,
      priority_score: 85,
      sent_at: new Date().toISOString(),
      viewed: false,
      purchased: false,
      item: {
        id: 303,
        fruit_type: 'Banana',
        variety: 'Organic',
        quantity: 22,
        original_price: 3.99,
        current_price: 2.49,
        discount_percentage: 38,
        freshness: {
          freshness_score: 86,
          status: 'fresh',
          predicted_expiry_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString()
        }
      },
      reason: {
        match_type: 'favorite_fruit',
        fruit: 'Banana',
        reasoning: 'Organic bananas on sale - great for your morning routine!',
        discount: 38
      }
    }
  ]
};

export const mockPurchases = {
  'abc': [
    {
      id: 1,
      inventory_id: 99,
      quantity: 2,
      price_paid: 4.98,
      discount_applied: 38,
      purchase_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      knot_transaction_id: null,
      fruit_type: 'Banana'
    }
  ],
  'def': [
    {
      id: 2,
      inventory_id: 98,
      quantity: 3,
      price_paid: 11.97,
      discount_applied: 33,
      purchase_date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      knot_transaction_id: null,
      fruit_type: 'Orange'
    }
  ],
  'ghi': [
    {
      id: 3,
      inventory_id: 97,
      quantity: 1,
      price_paid: 2.99,
      discount_applied: 40,
      purchase_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      knot_transaction_id: null,
      fruit_type: 'Pear'
    }
  ]
};

export const mockKnotTransactions = {
  'abc': [
    {
      id: 'knot_tx_1',
      external_id: 'abc_order_123',
      datetime: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      url: 'https://example.com/order/123',
      order_status: 'delivered',
      price: {
        sub_total: '18.95',
        total: '20.50',
        currency: 'USD'
      },
      products: [
        {
          external_id: 'prod_1',
          name: 'Organic Bananas',
          quantity: 3,
          price: {
            sub_total: '7.47',
            total: '7.47',
            unit_price: '2.49'
          }
        },
        {
          external_id: 'prod_2',
          name: 'Honeycrisp Apples',
          quantity: 2,
          price: {
            sub_total: '7.98',
            total: '7.98',
            unit_price: '3.99'
          }
        }
      ]
    }
  ],
  'def': [
    {
      id: 'knot_tx_2',
      external_id: 'def_order_456',
      datetime: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
      url: 'https://example.com/order/456',
      order_status: 'delivered',
      price: {
        sub_total: '19.95',
        total: '21.50',
        currency: 'USD'
      },
      products: [
        {
          external_id: 'prod_3',
          name: 'Valencia Oranges',
          quantity: 4,
          price: {
            sub_total: '15.96',
            total: '15.96',
            unit_price: '3.99'
          }
        },
        {
          external_id: 'prod_4',
          name: 'Organic Bananas',
          quantity: 2,
          price: {
            sub_total: '4.98',
            total: '4.98',
            unit_price: '2.49'
          }
        }
      ]
    }
  ],
  'ghi': [
    {
      id: 'knot_tx_3',
      external_id: 'ghi_order_789',
      datetime: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      url: 'https://example.com/order/789',
      order_status: 'delivered',
      price: {
        sub_total: '25.90',
        total: '28.00',
        currency: 'USD'
      },
      products: [
        {
          external_id: 'prod_5',
          name: 'Bartlett Pears',
          quantity: 4,
          price: {
            sub_total: '11.96',
            total: '11.96',
            unit_price: '2.99'
          }
        },
        {
          external_id: 'prod_6',
          name: 'Gala Apples',
          quantity: 3,
          price: {
            sub_total: '10.47',
            total: '10.47',
            unit_price: '3.49'
          }
        }
      ]
    }
  ]
};
