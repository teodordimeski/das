# Database Connector Module

## Overview

A clean Python module using SQLAlchemy ORM to connect to PostgreSQL and retrieve OHLCV daily data for cryptocurrency symbols.

## Features

✅ **SQLAlchemy ORM** - Modern, type-safe database access  
✅ **PostgreSQL Connection** - Connects to your cryptoCoins database  
✅ **OHLCV Data Retrieval** - Fetches symbol, date, open, high, low, close, volume  
✅ **Ordered Results** - Data returned ordered by date ascending  
✅ **Flexible Filtering** - Optional date range and limit parameters  
✅ **Pandas Integration** - Returns data as pandas DataFrame  

## Installation

SQLAlchemy is already included in `requirements.txt`. Install with:

```powershell
cd Domasna3\python_filters
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from database_connector import get_ohlcv_data

# Get all OHLCV data for a symbol
df = get_ohlcv_data('BTCUSDT')
print(df.head())
```

### With Date Filtering

```python
from database_connector import get_ohlcv_data
from datetime import datetime, timedelta

# Get last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

df = get_ohlcv_data('ETHUSDT', start_date=start_date, end_date=end_date)
print(df)
```

### With Limit

```python
# Get first 100 records
df = get_ohlcv_data('BTCUSDT', limit=100)
```

### Advanced Usage - Using DatabaseConnector Class

```python
from database_connector import DatabaseConnector
from datetime import datetime

# Create connector with custom settings
connector = DatabaseConnector(
    host='localhost',
    port=5432,
    database='cryptoCoins',
    user='postgres',
    password='admin'
)

# Get data
df = connector.get_ohlcv_data('BTCUSDT')

# Get list of all symbols
symbols = connector.get_symbols_list()
print(f"Available symbols: {symbols}")

# Get count of records
count = connector.get_data_count('BTCUSDT')
print(f"BTCUSDT has {count} records")
```

## Command Line Usage

```powershell
python database_connector.py BTCUSDT
```

This will:
- Fetch all OHLCV data for BTCUSDT
- Display first 5 and last 5 records
- Show date range
- Display data summary statistics

## Return Format

The function returns a pandas DataFrame with columns:

- `symbol` - Cryptocurrency symbol (e.g., 'BTCUSDT')
- `date` - Date (datetime)
- `open` - Opening price (float)
- `high` - Highest price (float)
- `low` - Lowest price (float)
- `close` - Closing price (float)
- `volume` - Trading volume (float)

Data is **ordered by date ascending**.

## Configuration

The module uses environment variables for database configuration:

- `DB_HOST` (default: 'localhost')
- `DB_PORT` (default: '5432')
- `DB_NAME` (default: 'cryptoCoins')
- `DB_USER` (default: 'postgres')
- `DB_PASSWORD` (default: 'admin')

You can override these by:
1. Setting environment variables
2. Passing parameters to `DatabaseConnector()` constructor

## Integration with LSTM Predictor

The LSTM predictor can use this module instead of direct psycopg2:

```python
from database_connector import get_ohlcv_data

# Instead of get_historical_data()
df = get_ohlcv_data('BTCUSDT')
```

## Error Handling

The module raises exceptions with descriptive error messages:
- Connection errors
- Query errors
- Missing data errors

Always wrap calls in try-except blocks:

```python
try:
    df = get_ohlcv_data('BTCUSDT')
except Exception as e:
    print(f"Error: {e}")
```

## Requirements

- Python 3.8+
- SQLAlchemy 2.0+
- pandas
- psycopg2-binary (PostgreSQL driver)

All dependencies are in `requirements.txt`.



