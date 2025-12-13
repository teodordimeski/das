# Train Model Script

## Overview

`train_model.py` is a standalone script that trains LSTM models to predict cryptocurrency Close prices. It loads data from PostgreSQL, normalizes it, creates 60-day lookback sequences, trains the model, and saves both the model and scaler.

## Features

✅ **CLI Argument** - Accepts crypto symbol as command-line argument  
✅ **PostgreSQL Integration** - Loads OHLCV data using SQLAlchemy  
✅ **Data Normalization** - MinMaxScaler normalization to [0, 1] range  
✅ **60-Day Lookback** - Creates sequences with 60-day lookback period  
✅ **LSTM Training** - 3-layer LSTM architecture to predict Close price  
✅ **Model Persistence** - Saves model (.h5) and scaler (.pkl) per symbol  

## Usage

### Basic Usage

```powershell
cd Domasna3\python_filters
python train_model.py BTCUSDT
```

### Training Multiple Symbols

```powershell
python train_model.py BTCUSDT
python train_model.py ETHUSDT
python train_model.py XRPUSDT
```

## What It Does

1. **Loads Data**: Fetches OHLCV data from PostgreSQL using `database_connector`
2. **Normalizes**: Scales all features (open, high, low, close, volume) to [0, 1]
3. **Creates Sequences**: Builds 60-day lookback sequences for LSTM input
4. **Splits Data**: 70% training, 30% validation
5. **Trains Model**: 3-layer LSTM with dropout regularization
6. **Saves Output**: Model and scaler saved to `lstm_models/` directory

## Model Architecture

```
Input: (60 days, 5 features)
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
Dense: 1 unit (Close price prediction)
```

## Output Files

After training, the following files are saved in `lstm_models/`:

- `{SYMBOL}_model.h5` - Trained Keras model
- `{SYMBOL}_scaler.pkl` - Fitted MinMaxScaler for inverse transformation
- `{SYMBOL}_checkpoint.h5` - Best model checkpoint (temporary)

**Example:**
- `BTCUSDT_model.h5`
- `BTCUSDT_scaler.pkl`

## Configuration

You can modify these constants in the script:

```python
LOOKBACK_PERIOD = 60      # 60-day lookback sequences
TRAIN_SPLIT = 0.7         # 70% training, 30% validation
EPOCHS = 50               # Training epochs
BATCH_SIZE = 32           # Batch size
LSTM_UNITS = 50           # LSTM units per layer
DROPOUT_RATE = 0.2        # Dropout rate
```

## Requirements

- Minimum data: 110 records (60 for lookback + 50 for training)
- Database must be populated (run Filter1 first)
- All dependencies from `requirements.txt` installed

## Training Process

The script will:

1. ✅ Load and validate data
2. ✅ Normalize features
3. ✅ Create sequences
4. ✅ Split train/validation
5. ✅ Build model architecture
6. ✅ Train with early stopping
7. ✅ Save model and scaler

**Training time**: ~2-5 minutes per symbol (depending on data size)

## Example Output

```
============================================================
Training LSTM Model for BTCUSDT
============================================================

[1/6] Loading OHLCV data from PostgreSQL for BTCUSDT...
✅ Loaded 3650 records
   Date range: 2020-01-01 to 2024-12-12

[2/6] Normalizing data...
✅ Data normalized to [0, 1] range

[3/6] Creating 60-day lookback sequences...
✅ Created 3590 sequences
   Input shape: (3590, 60, 5)
   Target shape: (3590,)

[4/6] Splitting data (70% train, 30% validation)...
✅ Training samples: 2513
✅ Validation samples: 1077

[5/6] Building LSTM model...
✅ Model built
   Architecture: 3 LSTM layers (50 units each) + Dense output

[6/6] Training LSTM model...
Training model for BTCUSDT...
  Training samples: 2513
  Validation samples: 1077
  Epochs: 50, Batch size: 32
...
Model saved to: lstm_models/BTCUSDT_model.h5
Scaler saved to: lstm_models/BTCUSDT_scaler.pkl

============================================================
Training Summary
============================================================
Final Training Loss: 0.000123
Final Validation Loss: 0.000145
Best Validation Loss: 0.000142 (epoch 23)

Model files saved:
  - lstm_models/BTCUSDT_model.h5
  - lstm_models/BTCUSDT_scaler.pkl
============================================================
✅ Training completed successfully!
```

## Using Trained Models

Trained models can be loaded and used for predictions:

```python
from tensorflow.keras.models import load_model
import pickle

# Load model
model = load_model('lstm_models/BTCUSDT_model.h5')

# Load scaler
with open('lstm_models/BTCUSDT_scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)
```

## Notes

- Models are trained per symbol
- Early stopping prevents overfitting
- Best model weights are saved automatically
- Scaler is required for inverse transformation of predictions



