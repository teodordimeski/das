# LSTM Price Prediction Feature

## Overview

This feature implements LSTM (Long Short-Term Memory) neural network for predicting cryptocurrency prices using historical OHLCV data from the database.

## Implementation Details

### Features Implemented

✅ **Data Preparation**
- Fetches historical price data (Open, High, Low, Close, Volume) from PostgreSQL
- Normalizes data using MinMaxScaler (0-1 range)
- Creates sequences with configurable lookback period

✅ **Data Split**
- 70% for training
- 30% for validation

✅ **Lookback Period**
- Configurable (default: 30 days)
- Can be adjusted via API parameter (10-100 days)

✅ **LSTM Model Training**
- 3-layer LSTM architecture with dropout regularization
- Uses Mean Squared Error (MSE) as loss function
- Adam optimizer
- Early stopping to prevent overfitting
- Model checkpointing for best weights

✅ **Evaluation Metrics**
- **RMSE** (Root Mean Squared Error)
- **MAPE** (Mean Absolute Percentage Error)
- **R-squared** (Coefficient of Determination)

✅ **Future Predictions**
- Generates predictions for configurable number of future days (default: 7)
- Returns predicted prices with dates

### Technology Stack

- **Python**: TensorFlow/Keras for LSTM implementation
- **Java**: Spring Boot REST API
- **Database**: PostgreSQL for historical data storage

## API Endpoint

### GET `/api/lstm/{symbol}`

Get LSTM price predictions for a cryptocurrency symbol.

**Parameters:**
- `symbol` (path): Cryptocurrency symbol (e.g., BTCUSDT, ETHUSDT)
- `lookback` (query, optional): Lookback period in days (default: 30, range: 10-100)
- `days` (query, optional): Number of future days to predict (default: 7, range: 1-30)

**Example Request:**
```
GET http://localhost:8080/api/lstm/BTCUSDT?lookback=30&days=7
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "lookbackPeriod": 30,
  "trainingSamples": 2450,
  "validationSamples": 1050,
  "lastPrice": 43250.50,
  "lastDate": "2024-01-15",
  "metrics": {
    "rmse": 125.34,
    "mape": 2.45,
    "r2Score": 0.92
  },
  "predictions": [
    {
      "date": "2024-01-16",
      "predictedPrice": 43500.25
    },
    {
      "date": "2024-01-17",
      "predictedPrice": 43750.80
    }
    // ... more predictions
  ]
}
```

## Installation

### 1. Install Python Dependencies

```powershell
cd Domasna3\python_filters
pip install -r requirements.txt
```

This will install:
- `tensorflow>=2.15.0` - LSTM implementation
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical operations
- `scikit-learn>=1.3.0` - Data preprocessing and metrics

### 2. Model Storage

Trained models are saved in `python_filters/lstm_models/` directory (created automatically).

## Usage

### First Time Usage

1. **Ensure database has historical data** (Filter1 should have populated it)
2. **Call the API endpoint** with a symbol:
   ```bash
   curl http://localhost:8080/api/lstm/BTCUSDT
   ```
3. **First prediction will:**
   - Fetch historical data from database
   - Train a new LSTM model (takes 2-5 minutes)
   - Save the model for future use
   - Return predictions and metrics

### Subsequent Usage

- If model exists, it will be reused (faster)
- Models are cached per symbol
- To retrain, delete the model file in `lstm_models/` directory

## Model Architecture

```
Input Layer: (lookback_period, 5 features)
    ↓
LSTM Layer 1: 50 units, return_sequences=True
    ↓
Dropout: 0.2
    ↓
LSTM Layer 2: 50 units, return_sequences=True
    ↓
Dropout: 0.2
    ↓
LSTM Layer 3: 50 units
    ↓
Dropout: 0.2
    ↓
Dense Layer: 1 unit (predicted price)
```

## Performance Considerations

- **Training Time**: 2-5 minutes for first prediction (model training)
- **Prediction Time**: < 1 second for subsequent predictions
- **Memory**: Models are ~2-5 MB each
- **Data Requirements**: Minimum 50 + lookback_period data points

## Error Handling

The API returns appropriate HTTP status codes:
- **200 OK**: Successful prediction
- **400 Bad Request**: Invalid parameters or insufficient data
- **500 Internal Server Error**: Model training/prediction errors

## Integration with Frontend

The frontend can call this endpoint to display:
- Future price predictions
- Model accuracy metrics (RMSE, MAPE, R²)
- Prediction confidence indicators

## Notes

- Models are trained per symbol
- Training uses early stopping to prevent overfitting
- Predictions are based on historical patterns
- **Disclaimer**: Predictions are for analysis purposes only, not financial advice



