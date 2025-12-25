#!/usr/bin/env python3

import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model, save_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from database_connector import get_ohlcv_data
import warnings
warnings.filterwarnings('ignore')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(SCRIPT_DIR, "lstm_models")
META_SUFFIX = "_meta.json"
# Retrain if model older than this many days OR if DB has newer data
RETRAIN_DAYS = int(os.getenv("LSTM_RETRAIN_DAYS", "7"))

# Configuration (matching train_model.py)
LOOKBACK_PERIOD = 60  # 60-day lookback sequences
TRAIN_SPLIT = 0.7  # 70% for training, 30% for validation
EPOCHS = 50
BATCH_SIZE = 32
LSTM_UNITS = 50
DROPOUT_RATE = 0.2


def normalize_data(df):
    """Normalize OHLCV data using MinMaxScaler"""
    features = ['open', 'high', 'low', 'close', 'volume']
    data = df[features].values
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    return scaled_data, scaler


def create_sequences(data, lookback_period, target_column_idx=3):
    """Create sequences for LSTM training"""
    X, y = [], []
    for i in range(lookback_period, len(data)):
        X.append(data[i - lookback_period:i])
        y.append(data[i, target_column_idx])
    return np.array(X), np.array(y)


def build_lstm_model(input_shape, units=LSTM_UNITS, dropout=DROPOUT_RATE):
    """Build LSTM model architecture"""
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


def train_model_if_needed(symbol, df):
    """Train a model if it doesn't exist, return model, scaler, and lookback_period"""
    model_path = os.path.join(MODELS_DIR, f"{symbol}_model.h5")
    scaler_path = os.path.join(MODELS_DIR, f"{symbol}_scaler.pkl")
    
    # Check if model exists
    meta_path = os.path.join(MODELS_DIR, f"{symbol}{META_SUFFIX}")
    model_exists = os.path.exists(model_path) and os.path.exists(scaler_path)
    if model_exists:
        try:
            print(f"Loading pre-trained model for {symbol}...", file=sys.stderr)
            model = load_model(model_path)
            with open(scaler_path, 'rb') as f:
                scaler = pickle.load(f)

            # Get lookback period from model
            input_shape = model.input_shape
            if input_shape and len(input_shape) >= 2:
                lookback_period = int(input_shape[1] if input_shape[1] else input_shape[0])
            else:
                lookback_period = LOOKBACK_PERIOD

            # Load metadata if available to decide if retraining is needed
            needs_retrain = False
            try:
                if os.path.exists(meta_path):
                    with open(meta_path, 'r') as mf:
                        meta = json.load(mf)
                    # Compare DB last date with metadata last_data_date
                    db_last = pd.to_datetime(df['date'].max())
                    meta_last = pd.to_datetime(meta.get('last_data_date')) if meta.get('last_data_date') else None
                    last_trained = pd.to_datetime(meta.get('last_trained')) if meta.get('last_trained') else None

                    if meta_last is None:
                        needs_retrain = True
                    else:
                        if db_last > meta_last:
                            print(f"Detected newer DB data (db:{db_last.date()} > meta:{meta_last.date()}) -> retrain needed", file=sys.stderr)
                            needs_retrain = True
                        elif last_trained is not None and (datetime.utcnow() - pd.to_datetime(last_trained).to_pydatetime()) > timedelta(days=RETRAIN_DAYS):
                            print(f"Model older than {RETRAIN_DAYS} days (last_trained={last_trained.date()}) -> retrain recommended", file=sys.stderr)
                            needs_retrain = True
                else:
                    # No metadata file => safer to retrain
                    print(f"No metadata found for {symbol} -> retrain recommended", file=sys.stderr)
                    needs_retrain = True
            except Exception as e:
                print(f"⚠️  Failed to read meta for {symbol}: {e} -> retrain recommended", file=sys.stderr)
                needs_retrain = True

            if needs_retrain:
                print(f"Retraining model for {symbol} due to freshness policy...", file=sys.stderr)
                # fall through to training logic below
            else:
                print(f"Loaded pre-trained model (lookback={lookback_period})", file=sys.stderr)
                return model, scaler, lookback_period
        except Exception as e:
            print(f"Error loading model: {e}. Will train new one.", file=sys.stderr)
    
    # Model doesn't exist or failed to load, train a new one
    print(f"Training new model for {symbol}...", file=sys.stderr)
    
    # Check minimum data requirement
    min_required = LOOKBACK_PERIOD + 50
    if len(df) < min_required:
        raise ValueError(f"Insufficient data for training. Need at least {min_required} records, got {len(df)}")
    
    # Normalize data
    scaled_data, scaler = normalize_data(df)
    
    # Create sequences
    X, y = create_sequences(scaled_data, LOOKBACK_PERIOD)
    
    # Split data
    split_idx = int(len(X) * TRAIN_SPLIT)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    # Build model
    input_shape = (LOOKBACK_PERIOD, 5)
    model = build_lstm_model(input_shape, LSTM_UNITS, DROPOUT_RATE)
    
    # Prepare callbacks
    os.makedirs(MODELS_DIR, exist_ok=True)
    checkpoint_path = os.path.join(MODELS_DIR, f"{symbol}_checkpoint.h5")
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=0),
        ModelCheckpoint(checkpoint_path, monitor='val_loss', save_best_only=True, verbose=0)
    ]
    
    # Train model
    print(f"Training with {len(X_train)} training samples, {len(X_val)} validation samples...", file=sys.stderr)
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=0
    )
    
    # Load best weights
    if os.path.exists(checkpoint_path):
        model.load_weights(checkpoint_path)
    
    # Save model and scaler
    save_model(model, model_path)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    # Save metadata about training and data freshness
    try:
        meta = {
            'last_trained': datetime.utcnow().isoformat(),
            'last_data_date': pd.to_datetime(df['date'].max()).isoformat(),
            'training_samples': len(X_train),
            'validation_samples': len(X_val),
            'lookback_period': LOOKBACK_PERIOD
        }
        with open(os.path.join(MODELS_DIR, f"{symbol}{META_SUFFIX}"), 'w') as mf:
            json.dump(meta, mf)
        print(f"Saved metadata: {os.path.join(MODELS_DIR, f'{symbol}{META_SUFFIX}')}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Failed to save metadata for {symbol}: {e}", file=sys.stderr)
    
    print(f"Model trained and saved: {model_path}", file=sys.stderr)
    
    return model, scaler, LOOKBACK_PERIOD


def prepare_prediction_data(df, scaler, lookback_period):
    features = ['open', 'high', 'low', 'close', 'volume']
    
    if len(df) < lookback_period:
        raise ValueError(f"Insufficient data. Need at least {lookback_period} days, got {len(df)}")
    
    last_n_days = df[features].tail(lookback_period).values
    normalized = scaler.transform(last_n_days)
    sequence = normalized.reshape(1, lookback_period, 5)
    
    return sequence


def predict_next_close(model, sequence, scaler):
    prediction_normalized = model.predict(sequence, verbose=0)
    
    dummy = np.zeros((1, 5))
    dummy[0, 3] = prediction_normalized[0, 0]
    
    predicted_values = scaler.inverse_transform(dummy)
    predicted_close = float(predicted_values[0, 3])
    
    return predicted_close


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Symbol argument required",
            "usage": "python predict.py <SYMBOL>",
            "example": "python predict.py BTCUSDT"
        }))
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    
    try:
        # Get data first
        df = get_ohlcv_data(symbol)
        
        if df.empty:
            print(json.dumps({
                "error": f"No data found for symbol {symbol}"
            }))
            sys.exit(1)
        
        # Train model if needed (or load existing)
        model, scaler, lookback_period = train_model_if_needed(symbol, df)
        
        # Check if we have enough data for prediction
        if len(df) < lookback_period:
            print(json.dumps({
                "error": f"Insufficient data. Need at least {lookback_period} days, got {len(df)}"
            }))
            sys.exit(1)
        
        # Prepare last N days for prediction
        df = df.tail(lookback_period).reset_index(drop=True)
        
        sequence = prepare_prediction_data(df, scaler, lookback_period)
        predicted_close = predict_next_close(model, sequence, scaler)
        
        result = {
            "symbol": symbol,
            "predicted_close": round(predicted_close, 2)
        }
        
        print(json.dumps(result, indent=2))
        
    except ValueError as e:
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

