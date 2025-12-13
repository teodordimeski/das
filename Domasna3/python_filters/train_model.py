#!/usr/bin/env python3
"""
LSTM Model Training Script

This script trains an LSTM model to predict cryptocurrency Close prices.
It loads OHLCV data from PostgreSQL, normalizes it, creates 60-day lookback
sequences, trains the model, and saves both the model and scaler.

Usage:
    python train_model.py BTCUSDT
    python train_model.py ETHUSDT
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, save_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import warnings
warnings.filterwarnings('ignore')

# Import database connector
from database_connector import get_ohlcv_data

# Configuration
LOOKBACK_PERIOD = 60  # 60-day lookback sequences
TRAIN_SPLIT = 0.7  # 70% for training, 30% for validation
MODELS_DIR = "lstm_models"
EPOCHS = 50
BATCH_SIZE = 32
LSTM_UNITS = 50
DROPOUT_RATE = 0.2


def normalize_data(df):
    """
    Normalize OHLCV data using MinMaxScaler
    
    Args:
        df: DataFrame with OHLCV columns (open, high, low, close, volume)
    
    Returns:
        scaled_data: Normalized numpy array
        scaler: Fitted MinMaxScaler for inverse transformation
    """
    # Select features: Open, High, Low, Close, Volume
    features = ['open', 'high', 'low', 'close', 'volume']
    data = df[features].values
    
    # Normalize to [0, 1] range
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    
    return scaled_data, scaler


def create_sequences(data, lookback_period, target_column_idx=3):
    """
    Create sequences for LSTM training
    
    Args:
        data: Normalized data array
        lookback_period: Number of days to look back (60)
        target_column_idx: Index of target column (3 = close price)
    
    Returns:
        X: Input sequences (samples, lookback_period, features)
        y: Target values (samples,)
    """
    X, y = [], []
    
    for i in range(lookback_period, len(data)):
        # Input: lookback_period days of all features
        X.append(data[i - lookback_period:i])
        # Target: close price of current day
        y.append(data[i, target_column_idx])
    
    return np.array(X), np.array(y)


def build_lstm_model(input_shape, units=LSTM_UNITS, dropout=DROPOUT_RATE):
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
        Dense(units=1)  # Predict single value (close price)
    ])
    
    model.compile(
        optimizer='adam',
        loss='mean_squared_error',
        metrics=['mae']
    )
    
    return model


def train_lstm_model(model, X_train, y_train, X_val, y_val, symbol, epochs=EPOCHS, batch_size=BATCH_SIZE):
    """
    Train the LSTM model
    
    Args:
        model: Compiled Keras model
        X_train: Training input sequences
        y_train: Training targets
        X_val: Validation input sequences
        y_val: Validation targets
        symbol: Cryptocurrency symbol (for model saving)
        epochs: Number of training epochs
        batch_size: Batch size for training
    
    Returns:
        history: Training history
        trained_model: Trained model
    """
    # Create models directory if it doesn't exist
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Model file paths
    model_path = os.path.join(MODELS_DIR, f"{symbol}_model.h5")
    checkpoint_path = os.path.join(MODELS_DIR, f"{symbol}_checkpoint.h5")
    
    # Callbacks
    callbacks = [
        EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True,
            verbose=1
        ),
        ModelCheckpoint(
            checkpoint_path,
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        )
    ]
    
    # Train the model
    print(f"Training model for {symbol}...")
    print(f"  Training samples: {len(X_train)}")
    print(f"  Validation samples: {len(X_val)}")
    print(f"  Epochs: {epochs}, Batch size: {batch_size}")
    
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=callbacks,
        verbose=1
    )
    
    # Load best model from checkpoint
    if os.path.exists(checkpoint_path):
        model.load_weights(checkpoint_path)
        print(f"Loaded best model weights from checkpoint")
    
    # Save final model
    save_model(model, model_path)
    print(f"Model saved to: {model_path}")
    
    return history, model


def save_scaler(scaler, symbol):
    """
    Save the scaler to disk
    
    Args:
        scaler: Fitted MinMaxScaler
        symbol: Cryptocurrency symbol
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    scaler_path = os.path.join(MODELS_DIR, f"{symbol}_scaler.pkl")
    
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    
    print(f"Scaler saved to: {scaler_path}")


def main():
    """Main training function"""
    if len(sys.argv) < 2:
        print("Usage: python train_model.py <SYMBOL>")
        print("Example: python train_model.py BTCUSDT")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    
    print("=" * 60)
    print(f"Training LSTM Model for {symbol}")
    print("=" * 60)
    
    try:
        # Step 1: Load OHLCV data from PostgreSQL
        print(f"\n[1/6] Loading OHLCV data from PostgreSQL for {symbol}...")
        df = get_ohlcv_data(symbol)
        
        if df.empty:
            print(f"[ERROR] No data found for symbol {symbol}")
            sys.exit(1)
        
        print(f"[OK] Loaded {len(df)} records")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        
        # Check minimum data requirement
        min_required = LOOKBACK_PERIOD + 50  # Need at least 60 + 50 for training
        if len(df) < min_required:
            print(f"[ERROR] Insufficient data. Need at least {min_required} records, got {len(df)}")
            sys.exit(1)
        
        # Step 2: Normalize data
        print(f"\n[2/6] Normalizing data...")
        scaled_data, scaler = normalize_data(df)
        print(f"[OK] Data normalized to [0, 1] range")
        
        # Step 3: Create 60-day lookback sequences
        print(f"\n[3/6] Creating {LOOKBACK_PERIOD}-day lookback sequences...")
        X, y = create_sequences(scaled_data, LOOKBACK_PERIOD)
        print(f"[OK] Created {len(X)} sequences")
        print(f"   Input shape: {X.shape}")
        print(f"   Target shape: {y.shape}")
        
        # Step 4: Split into training and validation sets
        print(f"\n[4/6] Splitting data (70% train, 30% validation)...")
        split_idx = int(len(X) * TRAIN_SPLIT)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        print(f"[OK] Training samples: {len(X_train)}")
        print(f"[OK] Validation samples: {len(X_val)}")
        
        # Step 5: Build LSTM model
        print(f"\n[5/6] Building LSTM model...")
        input_shape = (LOOKBACK_PERIOD, 5)  # 60 days, 5 features
        model = build_lstm_model(input_shape, LSTM_UNITS, DROPOUT_RATE)
        print(f"[OK] Model built")
        print(f"   Architecture: 3 LSTM layers ({LSTM_UNITS} units each) + Dense output")
        model.summary()
        
        # Step 6: Train the model
        print(f"\n[6/6] Training LSTM model...")
        history, trained_model = train_lstm_model(
            model, X_train, y_train, X_val, y_val, symbol, EPOCHS, BATCH_SIZE
        )
        
        # Save scaler
        save_scaler(scaler, symbol)
        
        # Print training summary
        print("\n" + "=" * 60)
        print("Training Summary")
        print("=" * 60)
        final_train_loss = history.history['loss'][-1]
        final_val_loss = history.history['val_loss'][-1]
        best_val_loss = min(history.history['val_loss'])
        best_epoch = history.history['val_loss'].index(best_val_loss) + 1
        
        print(f"Final Training Loss: {final_train_loss:.6f}")
        print(f"Final Validation Loss: {final_val_loss:.6f}")
        print(f"Best Validation Loss: {best_val_loss:.6f} (epoch {best_epoch})")
        print(f"\nModel files saved:")
        print(f"  - {MODELS_DIR}/{symbol}_model.h5")
        print(f"  - {MODELS_DIR}/{symbol}_scaler.pkl")
        print("=" * 60)
        print("[OK] Training completed successfully!")
        
    except Exception as e:
        print(f"\n[ERROR] Error during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()




