# EdgeCart Data Pipeline Architecture

## Overview
This document outlines the data flow through our Snowflake warehouse system for predictive waste intelligence.

## Pipeline Flow

### 1. KNOT API Integration
```
KNOT API → Pulls customer purchase data
   ↓
```
- **Source**: Knot Transaction Link API
- **Data**: Customer purchase history, transaction details
- **Format**: JSON via REST API
- **Frequency**: Real-time streaming

### 2. Initial Storage
```
Store in SNOWFLAKE warehouse
   ↓
```
- **Database**: `EDGECART_DB`
- **Schema**: `RAW_DATA`
- **Tables**:
  - `CUSTOMER_TRANSACTIONS`
  - `PURCHASE_HISTORY`
  - `MERCHANT_DATA`

### 3. Computer Vision Processing
```
CAMERA/CV → Detects freshness scores
   ↓
```
- **Input**: Camera feed from store produce sections
- **Processing**: YOLOv8 + Custom freshness model
- **Output**: Freshness scores (0-100), blemish detection, shelf life estimates

### 4. CV Data Storage
```
Store in SNOWFLAKE warehouse
   ↓
```
- **Database**: `EDGECART_DB`
- **Schema**: `INVENTORY_DATA`
- **Tables**:
  - `FRESHNESS_SCORES`
  - `INVENTORY_SNAPSHOTS`
  - `PRODUCE_METADATA`

### 5. AI Analysis Layer
```
AI AGENTS query SNOWFLAKE to:
   - Analyze patterns
   - Train ML models
   - Generate predictions
   ↓
```

#### Pattern Analysis
- **Agent**: Pattern Recognition Engine
- **Queries**: Time-series analysis on purchase behavior
- **Output**: Customer preference patterns, seasonal trends

#### ML Model Training
- **Agent**: AutoML Pipeline
- **Models**:
  - Waste prediction (XGBoost)
  - Demand forecasting (LSTM)
  - Price optimization (Random Forest)
- **Training Data**: Historical purchases + freshness scores

#### Prediction Generation
- **Agent**: Inference Service
- **Predictions**:
  - Per-customer recommendations
  - Store-level waste forecasts
  - Dynamic pricing suggestions

### 6. Results Storage
```
Results stored back in SNOWFLAKE
   ↓
```
- **Database**: `EDGECART_DB`
- **Schema**: `ANALYTICS`
- **Tables**:
  - `PREDICTIONS`
  - `RECOMMENDATIONS`
  - `MODEL_METRICS`

### 7. Dashboard Visualization
```
Dashboard pulls from SNOWFLAKE
```
- **Source**: Snowflake Analytics Schema
- **Consumers**:
  - Admin Dashboard
  - Customer Portal
  - Mobile App
- **Refresh**: Real-time via Snowflake Streams

## Data Architecture

```
┌─────────────────┐
│   KNOT API      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Camera/CV      │────▶│   SNOWFLAKE     │
│  Pipeline       │     │   Warehouse     │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌─────────┐  ┌─────────┐  ┌─────────┐
              │ RAW_DATA│  │INVENTORY│  │ANALYTICS│
              └─────────┘  └─────────┘  └─────────┘
                    │            │            │
                    └────────────┴────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │    AI Agents Query     │
                    │  - Pattern Analysis    │
                    │  - ML Training         │
                    │  - Predictions         │
                    └────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │      Dashboards        │
                    │   - Admin View         │
                    │   - Customer Portal    │
                    └────────────────────────┘
```

## Technologies

- **Warehouse**: Snowflake Cloud Data Platform
- **APIs**: Knot Transaction Link
- **CV**: YOLOv8, PyTorch, OpenCV
- **ML**: XGBoost, TensorFlow, scikit-learn
- **Orchestration**: Airflow + Snowflake Tasks
- **Visualization**: React + Recharts
