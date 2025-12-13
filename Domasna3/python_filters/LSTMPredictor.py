#!/usr/bin/env python3
"""
LSTM Price Prediction Module

This module implements LSTM (Long Short-Term Memory) neural network for predicting
cryptocurrency prices using historical OHLCV data.

Features:
- Data preparation from PostgreSQL database
- 70% training / 30% validation split
- Configurable lookback period (default: 30 days)
- LSTM model training with MSE loss function
- Evaluation metrics: RMSE, MAPE, R-squared
- Future price predictions
"""

import os
import sys
import json
import psycopg2
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, r2_score
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import warnings
warnings.filterwarnings('ignore')

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = "cryptoCoins"
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")

# Model configuration
DEFAULT_LOOKBACK = 30  # days
DEFAULT_TRAIN_SPLIT = 0.7  # 70% for training
DEFAULT_PREDICTION_DAYS = 7  # Predict next 7 days
MODEL_DIR = "lstm_models"


def get_historical_data(conn, symbol, limit=None):
    """Fetch historical price data from database"""
    cursor = conn.cursor()
    try:
        query = """
            SELECT date, open, high, low, close, volume, "quoteAssetVolume"
            FROM cryptosymbols
            WHERE symbol = %s
            ORDER BY date ASC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query, (symbol,))
        rows = cursor.fetchall()
        
        if not rows:
            return None
        
        df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close', 'volume', 'quoteAssetVolume'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        return df
    finally:
        cursor.close()


def prepare_data(df, lookback_period=DEFAULT_LOOKBACK, target_column='close'):
    """
    Prepare data for LSTM training
    
    Args:
        df: DataFrame with OHLCV data
        lookback_period: Number of days to look back
        target_column: Column to predict (default: 'close')
    
    Returns:
        X, y: Features and targets for training
        scaler: Fitted scaler for inverse transformation
    """
    # Select features: Open, High, Low, Close, Volume
    features = ['open', 'high', 'low', 'close', 'volume']
    data = df[features].values
    
    # Normalize the data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    
    # Create sequences
    X, y = [], []
    for i in range(lookback_period, len(scaled_data)):
        X.append(scaled_data[i-lookback_period:i])
        # Target is the close price
        close_idx = features.index(target_column)
        y.append(scaled_data[i, close_idx])
    
    X, y = np.array(X), np.array(y)
    
    return X, y, scaler


def split_data(X, y, train_split=DEFAULT_TRAIN_SPLIT):
    """Split data into training and validation sets"""
    split_idx = int(len(X) * train_split)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    return X_train, X_val, y_train, y_val


def build_lstm_model(input_shape, units=50, dropout=0.2):
    """
    Build LSTM model architecture
    
    Args:
        input_shape: Shape of input data (lookback_period, features)
        units: Number of LSTM units
        dropout: Dropout rate
    
    Returns:
        Compiled Keras model
    """
    model = Sequential([
        LSTM(units=units, return_sequences=True, input_shape=input_shape),
        Dropout(dropout),
        LSTM(units=units, return_sequences=True),
        Dropout(dropout),
        LSTM(units=units),
        Dropout(dropout),
        Dense(units=1)
    ])
    
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
    return model


def train_model(model, X_train, y_train, X_val, y_val, epochs=50, batch_size=32, symbol=None):
    """Train the LSTM model"""
    # Create model directory if it doesn't exist
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Callbacks
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
    ]
    
    if symbol:
        model_path = os.path.join(MODEL_DIR, f"{symbol}_lstm_model.h5")
        callbacks.append(ModelCheckpoint(model_path, monitor='val_loss', save_best_only=True, verbose=0))
    
    # Train the model
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=0
    )
    
    return history, model


def evaluate_model(model, X_val, y_val, scaler, target_column='close'):
    """
    Evaluate model performance
    
    Returns:
        Dictionary with RMSE, MAPE, and R-squared metrics
    """
    # Make predictions
    y_pred_scaled = model.predict(X_val, verbose=0)
    
    # Inverse transform predictions
    # Create dummy array for inverse transform
    dummy = np.zeros((len(y_pred_scaled), 5))  # 5 features
    close_idx = ['open', 'high', 'low', 'close', 'volume'].index(target_column)
    dummy[:, close_idx] = y_pred_scaled.flatten()
    y_pred = scaler.inverse_transform(dummy)[:, close_idx]
    
    # Inverse transform actual values
    dummy[:, close_idx] = y_val
    y_actual = scaler.inverse_transform(dummy)[:, close_idx]
    
    # Calculate metrics
    rmse = np.sqrt(mean_squared_error(y_actual, y_pred))
    mape = mean_absolute_percentage_error(y_actual, y_pred) * 100
    r2 = r2_score(y_actual, y_pred)
    
    return {
        'rmse': float(rmse),
        'mape': float(mape),
        'r2_score': float(r2),
        'predictions': y_pred.tolist(),
        'actual': y_actual.tolist()
    }


def predict_future(model, last_sequence, scaler, days=DEFAULT_PREDICTION_DAYS, target_column='close'):
    """
    Predict future prices
    
    Args:
        model: Trained LSTM model
        last_sequence: Last lookback_period days of data
        scaler: Fitted scaler
        days: Number of days to predict
        target_column: Column to predict
    
    Returns:
        List of predicted prices
    """
    predictions = []
    current_sequence = last_sequence.copy()
    features = ['open', 'high', 'low', 'close', 'volume']
    close_idx = features.index(target_column)
    
    for _ in range(days):
        # Predict next value
        next_pred_scaled = model.predict(current_sequence.reshape(1, *current_sequence.shape), verbose=0)
        
        # Create full feature vector for inverse transform
        dummy = np.zeros((1, 5))
        dummy[0, close_idx] = next_pred_scaled[0, 0]
        next_pred = scaler.inverse_transform(dummy)[0, close_idx]
        predictions.append(float(next_pred))
        
        # Update sequence: shift and add prediction
        # Use predicted close as all OHLC values (simplified approach)
        new_row = current_sequence[-1].copy()
        new_row[close_idx] = next_pred_scaled[0, 0]
        current_sequence = np.vstack([current_sequence[1:], new_row])
    
    return predictions


def main():
    """Main function to run LSTM prediction"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'error': 'Symbol argument required',
            'usage': 'python LSTMPredictor.py <symbol> [lookback_period] [prediction_days]'
        }))
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    lookback_period = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_LOOKBACK
    prediction_days = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_PREDICTION_DAYS
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        # Fetch historical data
        print(f"📥 Fetching historical data for {symbol}...", file=sys.stderr)
        df = get_historical_data(conn, symbol)
        
        if df is None or len(df) < lookback_period + 50:
            print(json.dumps({
                'error': f'Insufficient data for {symbol}. Need at least {lookback_period + 50} data points.'
            }))
            conn.close()
            sys.exit(1)
        
        print(f"✅ Found {len(df)} data points", file=sys.stderr)
        
        # Prepare data
        print(f"🔧 Preparing data with lookback period: {lookback_period}...", file=sys.stderr)
        X, y, scaler = prepare_data(df, lookback_period)
        
        # Split data
        X_train, X_val, y_train, y_val = split_data(X, y)
        print(f"📊 Training set: {len(X_train)}, Validation set: {len(X_val)}", file=sys.stderr)
        
        # Build model
        print("🏗️  Building LSTM model...", file=sys.stderr)
        model = build_lstm_model((lookback_period, 5))
        
        # Train model
        print("🎓 Training model...", file=sys.stderr)
        history, model = train_model(model, X_train, y_train, X_val, y_val, epochs=50, symbol=symbol)
        
        # Evaluate model
        print("📈 Evaluating model...", file=sys.stderr)
        metrics = evaluate_model(model, X_val, y_val, scaler)
        
        # Predict future
        print(f"🔮 Predicting next {prediction_days} days...", file=sys.stderr)
        last_sequence = X[-1]
        future_predictions = predict_future(model, last_sequence, scaler, days=prediction_days)
        
        # Get last actual price
        last_price = float(df['close'].iloc[-1])
        last_date = df['date'].iloc[-1].strftime('%Y-%m-%d')
        
        # Generate prediction dates
        prediction_dates = []
        current_date = pd.to_datetime(last_date)
        for i in range(1, prediction_days + 1):
            prediction_dates.append((current_date + timedelta(days=i)).strftime('%Y-%m-%d'))
        
        # Prepare response
        result = {
            'symbol': symbol,
            'lookback_period': lookback_period,
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'last_price': last_price,
            'last_date': last_date,
            'metrics': {
                'rmse': metrics['rmse'],
                'mape': metrics['mape'],
                'r2_score': metrics['r2_score']
            },
            'predictions': [
                {
                    'date': date,
                    'predicted_price': price
                }
                for date, price in zip(prediction_dates, future_predictions)
            ]
        }
        
        # Output JSON result
        print(json.dumps(result, indent=2))
        
        conn.close()
        
    except Exception as e:
        print(json.dumps({
            'error': str(e),
            'type': type(e).__name__
        }))
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

