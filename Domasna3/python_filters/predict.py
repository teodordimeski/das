#!/usr/bin/env python3

import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from database_connector import get_ohlcv_data

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(SCRIPT_DIR, "lstm_models")


def load_trained_model(symbol):
    model_path = os.path.join(MODELS_DIR, f"{symbol}_model.h5")
    scaler_path = os.path.join(MODELS_DIR, f"{symbol}_scaler.pkl")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}. Please train the model first using train_model.py")
    
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler not found: {scaler_path}. Please train the model first using train_model.py")
    
    model = load_model(model_path)
    
    input_shape = model.input_shape
    if input_shape is None or len(input_shape) < 2:
        raise ValueError(f"Cannot determine lookback period from model input shape: {input_shape}")
    
    lookback_dim = input_shape[1] if input_shape[1] is not None else input_shape[0]
    
    if lookback_dim is None:
        raise ValueError(f"Cannot determine lookback period from model input shape: {input_shape}")
    
    lookback_period = int(lookback_dim)
    
    if lookback_period <= 0:
        raise ValueError(f"Invalid lookback period inferred from model: {lookback_period}")
    
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    
    return model, scaler, lookback_period


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
        model, scaler, lookback_period = load_trained_model(symbol)
        
        df = get_ohlcv_data(symbol)
        
        if df.empty:
            print(json.dumps({
                "error": f"No data found for symbol {symbol}"
            }))
            sys.exit(1)
        
        if len(df) < lookback_period:
            print(json.dumps({
                "error": f"Insufficient data. Need at least {lookback_period} days, got {len(df)}"
            }))
            sys.exit(1)
        
        df = df.tail(lookback_period).reset_index(drop=True)
        
        sequence = prepare_prediction_data(df, scaler, lookback_period)
        predicted_close = predict_next_close(model, sequence, scaler)
        
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

