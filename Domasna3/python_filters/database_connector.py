#!/usr/bin/env python3
"""
Database Connector Module using SQLAlchemy

This module provides a clean interface to connect to PostgreSQL and retrieve
OHLCV daily data for cryptocurrency symbols using SQLAlchemy ORM.

Usage:
    from database_connector import get_ohlcv_data
    
    data = get_ohlcv_data('BTCUSDT')
    print(data)
"""

import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, String, Date, Numeric, select
from sqlalchemy.orm import declarative_base, sessionmaker
import pandas as pd

# Database configuration - can be overridden by environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "cryptoCoins")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")

# SQLAlchemy Base (SQLAlchemy 2.0 syntax)
Base = declarative_base()


class CryptoSymbol(Base):
    """
    SQLAlchemy model for cryptosymbols table
    Maps to the PostgreSQL table structure
    """
    __tablename__ = 'cryptosymbols'
    
    id = Column(Numeric, primary_key=True)
    symbol = Column(String(255), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Numeric, nullable=False)
    high = Column(Numeric, nullable=False)
    low = Column(Numeric, nullable=False)
    close = Column(Numeric, nullable=False)
    volume = Column(Numeric, nullable=False)
    
    # Additional columns that may exist in the table
    quoteAssetVolume = Column(Numeric, name='quoteAssetVolume')
    lastPrice_24h = Column(Numeric, name='lastPrice_24h')
    volume_24h = Column(Numeric, name='volume_24h')
    quoteVolume_24h = Column(Numeric, name='quoteVolume_24h')
    high_24h = Column(Numeric, name='high_24h')
    low_24h = Column(Numeric, name='low_24h')
    baseAsset = Column(String(255), name='baseAsset')
    quoteAsset = Column(String(255), name='quoteAsset')
    symbolUsed = Column(String(255), name='symbolUsed', nullable=False)


class DatabaseConnector:
    """
    Database connector class using SQLAlchemy
    Handles connection, session management, and data retrieval
    """
    
    def __init__(self, host=None, port=None, database=None, user=None, password=None):
        """
        Initialize database connector
        
        Args:
            host: Database host (default: from environment or 'localhost')
            port: Database port (default: from environment or '5432')
            database: Database name (default: from environment or 'cryptoCoins')
            user: Database user (default: from environment or 'postgres')
            password: Database password (default: from environment or 'admin')
        """
        self.host = host or DB_HOST
        self.port = port or DB_PORT
        self.database = database or DB_NAME
        self.user = user or DB_USER
        self.password = password or DB_PASSWORD
        
        # Create connection string
        self.connection_string = (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )
        
        # Create engine
        self.engine = create_engine(
            self.connection_string,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL query logging
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
    
    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
    
    def get_ohlcv_data(
        self, 
        symbol: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Get OHLCV daily data for a given cryptocurrency symbol
        
        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTCUSDT', 'ETHUSDT')
            start_date: Optional start date filter (datetime object)
            end_date: Optional end date filter (datetime object)
            limit: Optional limit on number of records
        
        Returns:
            pandas DataFrame with columns: symbol, date, open, high, low, close, volume
            Ordered by date ascending
        
        Raises:
            Exception: If database connection fails or query fails
        """
        session = self.get_session()
        try:
            # Build query
            query = select(
                CryptoSymbol.symbol,
                CryptoSymbol.date,
                CryptoSymbol.open,
                CryptoSymbol.high,
                CryptoSymbol.low,
                CryptoSymbol.close,
                CryptoSymbol.volume
            ).where(
                CryptoSymbol.symbol == symbol.upper()
            )
            
            # Apply date filters if provided
            if start_date:
                query = query.where(CryptoSymbol.date >= start_date.date())
            if end_date:
                query = query.where(CryptoSymbol.date <= end_date.date())
            
            # Order by date ascending
            query = query.order_by(CryptoSymbol.date.asc())
            
            # Apply limit if provided
            if limit:
                query = query.limit(limit)
            
            # Execute query and convert to DataFrame
            result = session.execute(query)
            rows = result.fetchall()
            
            if not rows:
                return pd.DataFrame(columns=['symbol', 'date', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=['symbol', 'date', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert numeric columns to float
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Ensure date is datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Sort by date (ascending) - redundant but ensures order
            df = df.sort_values('date').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            raise Exception(f"Error fetching OHLCV data for {symbol}: {str(e)}")
        finally:
            session.close()
    
    def get_symbols_list(self) -> List[str]:
        """
        Get list of all unique symbols in the database
        
        Returns:
            List of unique symbol strings
        """
        session = self.get_session()
        try:
            query = select(CryptoSymbol.symbol).distinct()
            result = session.execute(query)
            symbols = [row[0] for row in result.fetchall()]
            return sorted(symbols)
        except Exception as e:
            raise Exception(f"Error fetching symbols list: {str(e)}")
        finally:
            session.close()
    
    def get_data_count(self, symbol: str) -> int:
        """
        Get count of records for a given symbol
        
        Args:
            symbol: Cryptocurrency symbol
        
        Returns:
            Number of records for the symbol
        """
        session = self.get_session()
        try:
            from sqlalchemy import func
            query = select(func.count(CryptoSymbol.id)).where(
                CryptoSymbol.symbol == symbol.upper()
            )
            result = session.execute(query)
            count = result.scalar()
            return count or 0
        except Exception as e:
            raise Exception(f"Error counting records for {symbol}: {str(e)}")
        finally:
            session.close()


# Global connector instance (lazy initialization)
_connector = None


def get_connector() -> DatabaseConnector:
    """Get or create global database connector instance"""
    global _connector
    if _connector is None:
        _connector = DatabaseConnector()
    return _connector


def get_ohlcv_data(
    symbol: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: Optional[int] = None
) -> pd.DataFrame:
    """
    Convenience function to get OHLCV data for a symbol
    
    Args:
        symbol: Cryptocurrency symbol (e.g., 'BTCUSDT')
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Optional limit on number of records
    
    Returns:
        pandas DataFrame with OHLCV data ordered by date ascending
    
    Example:
        >>> df = get_ohlcv_data('BTCUSDT')
        >>> print(df.head())
        
        >>> from datetime import datetime, timedelta
        >>> end = datetime.now()
        >>> start = end - timedelta(days=30)
        >>> df = get_ohlcv_data('ETHUSDT', start_date=start, end_date=end)
    """
    connector = get_connector()
    return connector.get_ohlcv_data(symbol, start_date, end_date, limit)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python database_connector.py <symbol>")
        print("Example: python database_connector.py BTCUSDT")
        sys.exit(1)
    
    symbol = sys.argv[1]
    
    try:
        print(f"Fetching OHLCV data for {symbol}...")
        df = get_ohlcv_data(symbol)
        
        if df.empty:
            print(f"No data found for symbol: {symbol}")
        else:
            print(f"\nFound {len(df)} records")
            print(f"\nFirst 5 records:")
            print(df.head())
            print(f"\nLast 5 records:")
            print(df.tail())
            print(f"\nDate range: {df['date'].min()} to {df['date'].max()}")
            print(f"\nData summary:")
            print(df[['open', 'high', 'low', 'close', 'volume']].describe())
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

