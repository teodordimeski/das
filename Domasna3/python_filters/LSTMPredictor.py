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

# Note: This script will now also write `predict.py`-compatible artifacts in
# `lstm_models/` so the single-day prediction script can reuse models and
# scalers without retraining (files: {symbol}_model.h5, {symbol}_scaler.pkl,
# and {symbol}_meta.json).

import os
import sys
import json
import pickle
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


def get_model_paths(symbol, lookback_period):
    """Get model and scaler file paths for a symbol and lookback period"""
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, f"{symbol}_lstm_lb{lookback_period}_model.h5")
    scaler_path = os.path.join(MODEL_DIR, f"{symbol}_lstm_lb{lookback_period}_scaler.pkl")
    return model_path, scaler_path


def load_trained_model(symbol, lookback_period):
    """Load pre-trained model and scaler if they exist"""
    model_path, scaler_path = get_model_paths(symbol, lookback_period)
    
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        try:
            print(f"📂 Loading pre-trained model for {symbol} (lookback={lookback_period})...", file=sys.stderr)
            model = load_model(model_path)
            with open(scaler_path, 'rb') as f:
                scaler = pickle.load(f)
            print(f"✅ Loaded pre-trained model and scaler", file=sys.stderr)
            return model, scaler, True
        except Exception as e:
            print(f"⚠️  Error loading pre-trained model: {e}. Will train new model.", file=sys.stderr)
            return None, None, False
    
    return None, None, False


def save_model_and_scaler(model, scaler, symbol, lookback_period):
    """Save trained model and scaler to disk"""
    model_path, scaler_path = get_model_paths(symbol, lookback_period)
    
    try:
        model.save(model_path)
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
        print(f"💾 Saved model: {model_path}", file=sys.stderr)
        print(f"💾 Saved scaler: {scaler_path}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Warning: Failed to save model/scaler: {e}", file=sys.stderr)


def save_predict_compatibility(model, scaler, symbol, lookback_period, last_data_date=None, training_samples=None, validation_samples=None):
    """Save copies using the naming convention expected by `predict.py` and write metadata.

    This writes:
      - lstm_models/{symbol}_model.h5
      - lstm_models/{symbol}_scaler.pkl
      - lstm_models/{symbol}_meta.json
    """
    try:
        os.makedirs(MODEL_DIR, exist_ok=True)

        predict_model_path = os.path.join(MODEL_DIR, f"{symbol}_model.h5")
        predict_scaler_path = os.path.join(MODEL_DIR, f"{symbol}_scaler.pkl")
        meta_path = os.path.join(MODEL_DIR, f"{symbol}_meta.json")

        # Save model
        try:
            model.save(predict_model_path)
            print(f"💾 Saved predict-compatible model: {predict_model_path}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Failed to save predict-compatible model: {e}", file=sys.stderr)

        # Save scaler
        try:
            with open(predict_scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            print(f"💾 Saved predict-compatible scaler: {predict_scaler_path}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Failed to save predict-compatible scaler: {e}", file=sys.stderr)

        # Save metadata
        try:
            meta = {
                'last_trained': datetime.utcnow().isoformat(),
                'last_data_date': pd.to_datetime(last_data_date).isoformat() if last_data_date is not None else None,
                'lookback_period': lookback_period,
                'training_samples': training_samples,
                'validation_samples': validation_samples
            }
            with open(meta_path, 'w') as mf:
                json.dump(meta, mf)
            print(f"💾 Saved metadata: {meta_path}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️  Failed to save metadata for predict: {e}", file=sys.stderr)

    except Exception as e:
        print(f"⚠️  Unexpected error while saving predict-compatible artifacts: {e}", file=sys.stderr)


def train_model(model, X_train, y_train, X_val, y_val, epochs=50, batch_size=32, symbol=None, lookback_period=None):
    """Train the LSTM model"""
    # Create model directory if it doesn't exist
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Callbacks
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True),
    ]
    
    if symbol and lookback_period:
        model_path, _ = get_model_paths(symbol, lookback_period)
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
        
        # Try to load pre-trained model first
        model, scaler, model_loaded = load_trained_model(symbol, lookback_period)
        
        if model_loaded:
            # Model loaded, prepare data using the loaded scaler
            print(f"🔧 Preparing data with lookback period: {lookback_period} (using loaded scaler)...", file=sys.stderr)
            
            # Use the loaded scaler to transform current data
            features = ['open', 'high', 'low', 'close', 'volume']
            data = df[features].values
            scaled_data = scaler.transform(data)  # Use loaded scaler
            
            # Create sequences
            X, y = [], []
            for i in range(lookback_period, len(scaled_data)):
                X.append(scaled_data[i-lookback_period:i])
                close_idx = features.index('close')
                y.append(scaled_data[i, close_idx])
            
            X, y = np.array(X), np.array(y)
            
            # Split for evaluation (we still need validation set for metrics)
            X_train, X_val, y_train, y_val = split_data(X, y)
            print(f"📊 Using validation set: {len(X_val)} samples", file=sys.stderr)
            
            # Evaluate model
            print("📈 Evaluating model...", file=sys.stderr)
            metrics = evaluate_model(model, X_val, y_val, scaler)
        else:
            # No pre-trained model, train a new one
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
            history, model = train_model(model, X_train, y_train, X_val, y_val, epochs=50, symbol=symbol, lookback_period=lookback_period)
            
            # Save model and scaler
            save_model_and_scaler(model, scaler, symbol, lookback_period)
            
            # Evaluate model
            print("📈 Evaluating model...", file=sys.stderr)
            metrics = evaluate_model(model, X_val, y_val, scaler)
        
            # Ensure predict.py can reuse this model: save predict-compatible copies and metadata
            try:
                save_predict_compatibility(model, scaler, symbol, lookback_period,
                                          last_data_date=df['date'].max(),
                                          training_samples=len(X_train),
                                          validation_samples=len(X_val))
            except Exception as e:
                print(f"⚠️  Failed to save predict-compatible artifacts after loading model: {e}", file=sys.stderr)
            # Save predict-compatible copies & metadata so `predict.py` can pick them up
            try:
                save_predict_compatibility(model, scaler, symbol, lookback_period,
                                          last_data_date=df['date'].max(),
                                          training_samples=len(X_train),
                                          validation_samples=len(X_val))
            except Exception as e:
                print(f"⚠️  Failed to save predict-compatible artifacts after training: {e}", file=sys.stderr)
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
        # Use camelCase keys so Jackson on the Java side can map fields to DTOs
        result = {
            'symbol': symbol,
            'lookbackPeriod': lookback_period,
            'trainingSamples': len(X_train),
            'validationSamples': len(X_val),
            'lastPrice': last_price,
            'lastDate': last_date,
            'metrics': {
                'rmse': metrics['rmse'],
                'mape': metrics['mape'],
                'r2Score': metrics['r2_score'] if 'r2_score' in metrics else metrics.get('r2Score')
            },
            'predictions': [
                {
                    'date': date,
                    'predictedPrice': price
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




