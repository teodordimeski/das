#!/usr/bin/env python3
"""
LSTM Price Prediction Script

This script loads a trained LSTM model and generates a prediction for the next
closing price of a cryptocurrency symbol. The lookback period is automatically
inferred from the model's input shape, so it works with models trained with
any lookback period (30, 60, etc.).

Usage:
    python predict.py BTCUSDT
    python predict.py ETHUSDT
"""

import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from database_connector import get_ohlcv_data

# Configuration
MODELS_DIR = "lstm_models"


def load_trained_model(symbol):
    """
    Load trained LSTM model and scaler for a symbol
    
    Args:
        symbol: Cryptocurrency symbol
    
    Returns:
        model: Loaded Keras model
        scaler: Loaded MinMaxScaler
        lookback_period: Lookback period inferred from model input shape
    
    Raises:
        FileNotFoundError: If model or scaler files don't exist
        ValueError: If model input shape cannot be determined
    """
    model_path = os.path.join(MODELS_DIR, f"{symbol}_model.h5")
    scaler_path = os.path.join(MODELS_DIR, f"{symbol}_scaler.pkl")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}. Please train the model first using train_model.py")
    
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler not found: {scaler_path}. Please train the model first using train_model.py")
    
    # Load model
    model = load_model(model_path)
    
    # Infer lookback period from model input shape
    # Model input shape should be (None, lookback_period, 5) or (lookback_period, 5)
    input_shape = model.input_shape
    if input_shape is None or len(input_shape) < 2:
        raise ValueError(f"Cannot determine lookback period from model input shape: {input_shape}")
    
    # Input shape is typically (None, lookback_period, 5) or (lookback_period, 5)
    # The lookback period is the second dimension (index 1)
    # Handle both cases: (None, lookback_period, 5) and (lookback_period, 5)
    lookback_dim = input_shape[1] if input_shape[1] is not None else input_shape[0]
    
    if lookback_dim is None:
        raise ValueError(f"Cannot determine lookback period from model input shape: {input_shape}")
    
    lookback_period = int(lookback_dim)
    
    if lookback_period <= 0:
        raise ValueError(f"Invalid lookback period inferred from model: {lookback_period}")
    
    # Load scaler
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    
    return model, scaler, lookback_period


def prepare_prediction_data(df, scaler, lookback_period):
    """
    Prepare the last N days of data for prediction
    
    Args:
        df: DataFrame with OHLCV data (must have at least lookback_period rows)
        scaler: Fitted MinMaxScaler
        lookback_period: Number of days to use for prediction
    
    Returns:
        sequence: Normalized sequence ready for LSTM input (1, lookback_period, 5)
    """
    # Select features: Open, High, Low, Close, Volume
    features = ['open', 'high', 'low', 'close', 'volume']
    
    # Get last N days
    if len(df) < lookback_period:
        raise ValueError(f"Insufficient data. Need at least {lookback_period} days, got {len(df)}")
    
    last_n_days = df[features].tail(lookback_period).values
    
    # Normalize using the fitted scaler
    normalized = scaler.transform(last_n_days)
    
    # Reshape for LSTM: (1, lookback_period, features)
    sequence = normalized.reshape(1, lookback_period, 5)
    
    return sequence


def predict_next_close(model, sequence, scaler):
    """
    Predict the next closing price
    
    Args:
        model: Trained LSTM model
        sequence: Normalized input sequence (1, 60, 5)
        scaler: Fitted MinMaxScaler for inverse transformation
    
    Returns:
        predicted_close: Predicted closing price (float)
    """
    # Make prediction (returns normalized value)
    prediction_normalized = model.predict(sequence, verbose=0)
    
    # Inverse transform to get actual price
    # Create dummy array for inverse transform (scaler expects 5 features)
    dummy = np.zeros((1, 5))
    dummy[0, 3] = prediction_normalized[0, 0]  # Close price is at index 3
    
    # Inverse transform
    predicted_values = scaler.inverse_transform(dummy)
    predicted_close = float(predicted_values[0, 3])  # Extract close price
    
    return predicted_close


def main():
    """Main prediction function"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Symbol argument required",
            "usage": "python predict.py <SYMBOL>",
            "example": "python predict.py BTCUSDT"
        }))
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    
    try:
        # Step 1: Load trained model, scaler, and infer lookback period
        model, scaler, lookback_period = load_trained_model(symbol)
        
        # Step 2: Load OHLCV data from PostgreSQL
        # Get enough data to ensure we have the most recent N days (where N = lookback_period)
        # Data is ordered by date ascending, so we need to get all and take the tail
        df = get_ohlcv_data(symbol)
        
        if df.empty:
            print(json.dumps({
                "error": f"No data found for symbol {symbol}"
            }))
            sys.exit(1)
        
        # Ensure we have at least lookback_period days
        if len(df) < lookback_period:
            print(json.dumps({
                "error": f"Insufficient data. Need at least {lookback_period} days, got {len(df)}"
            }))
            sys.exit(1)
        
        # Get the last N days (most recent data - data is ordered by date ascending)
        df = df.tail(lookback_period).reset_index(drop=True)
        
        # Step 3: Prepare data for prediction
        sequence = prepare_prediction_data(df, scaler, lookback_period)
        
        # Step 4: Generate prediction
        predicted_close = predict_next_close(model, sequence, scaler)
        
        # Step 5: Output result as JSON
        result = {
            "symbol": symbol,
            "predicted_close": round(predicted_close, 2)
        }
        
        print(json.dumps(result, indent=2))
        
    except FileNotFoundError as e:
        print(json.dumps({
            "error": str(e)
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "type": type(e).__name__
        }))
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

