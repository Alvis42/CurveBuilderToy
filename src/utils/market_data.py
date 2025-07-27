"""
Market data handling utilities.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from ..core.instruments import IRSwap, IRFuture


def load_sample_data() -> pd.DataFrame:
    """
    Load sample market data for testing.
    
    Returns:
        DataFrame with sample market data
    """
    # Sample swap rates (annualized)
    sample_data = {
        'instrument_type': ['swap', 'swap', 'swap', 'swap', 'swap', 'swap'],
        'tenor': [0.5, 1.0, 2.0, 3.0, 5.0, 10.0],
        'rate': [0.025, 0.0275, 0.03, 0.0325, 0.035, 0.0375],
        'market_price': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # Par swaps
        'frequency': [2, 2, 2, 2, 2, 2]
    }
    
    return pd.DataFrame(sample_data)


def create_sample_instruments() -> List[IRSwap]:
    """
    Create sample interest rate swap instruments.
    
    Returns:
        List of IRSwap instruments
    """
    sample_data = load_sample_data()
    instruments = []
    
    for _, row in sample_data.iterrows():
        if row['instrument_type'] == 'swap':
            swap = IRSwap(
                start_date=0.0,
                maturity=row['tenor'],
                fixed_rate=row['rate'],
                frequency=row['frequency'],
                notional=1.0
            )
            instruments.append(swap)
    
    return instruments


def create_sample_futures() -> List[IRFuture]:
    """
    Create sample interest rate future instruments.
    
    Returns:
        List of IRFuture instruments
    """
    # Sample Eurodollar futures data
    futures_data = [
        {'start': 0.0, 'maturity': 0.25, 'price': 99.75},  # 3M future
        {'start': 0.25, 'maturity': 0.5, 'price': 99.50},   # 6M future
        {'start': 0.5, 'maturity': 0.75, 'price': 99.25},   # 9M future
        {'start': 0.75, 'maturity': 1.0, 'price': 99.00},   # 12M future
    ]
    
    instruments = []
    for data in futures_data:
        future = IRFuture(
            start_date=data['start'],
            maturity=data['maturity'],
            notional=1.0,
            contract_size=1.0
        )
        instruments.append(future)
    
    return instruments


def get_sample_market_prices() -> List[float]:
    """
    Get sample market prices for instruments.
    
    Returns:
        List of market prices
    """
    # For par swaps, market price is 0 (no upfront payment)
    swap_prices = [0.0] * 6
    
    # For futures, use the sample prices
    future_prices = [99.75, 99.50, 99.25, 99.00]
    
    return swap_prices + future_prices


def create_mixed_instruments() -> List:
    """
    Create a mix of swaps and futures for testing.
    
    Returns:
        List of mixed instruments
    """
    swaps = create_sample_instruments()
    futures = create_sample_futures()
    
    return swaps + futures


def save_sample_data_to_csv(filename: str = 'data/sample_data.csv'):
    """
    Save sample data to CSV file.
    
    Args:
        filename: Output filename
    """
    data = load_sample_data()
    data.to_csv(filename, index=False)
    print(f"Sample data saved to {filename}")


def load_market_data_from_csv(filename: str) -> pd.DataFrame:
    """
    Load market data from CSV file.
    
    Args:
        filename: Input CSV filename
        
    Returns:
        DataFrame with market data
    """
    try:
        data = pd.read_csv(filename)
        required_columns = ['instrument_type', 'tenor', 'rate']
        
        if not all(col in data.columns for col in required_columns):
            raise ValueError(f"CSV must contain columns: {required_columns}")
        
        return data
    except FileNotFoundError:
        print(f"File {filename} not found. Creating sample data.")
        save_sample_data_to_csv(filename)
        return load_sample_data()


def create_instruments_from_data(data: pd.DataFrame) -> List:
    """
    Create instruments from market data DataFrame.
    
    Args:
        data: DataFrame with market data
        
    Returns:
        List of instruments
    """
    instruments = []
    
    for _, row in data.iterrows():
        if row['instrument_type'] == 'swap':
            instrument = IRSwap(
                start_date=0.0,
                maturity=row['tenor'],
                fixed_rate=row['rate'],
                frequency=row.get('frequency', 2),
                notional=row.get('notional', 1.0)
            )
        elif row['instrument_type'] == 'future':
            instrument = IRFuture(
                start_date=row.get('start_date', 0.0),
                maturity=row['tenor'],
                notional=row.get('notional', 1.0),
                contract_size=row.get('contract_size', 1.0)
            )
        else:
            raise ValueError(f"Unknown instrument type: {row['instrument_type']}")
        
        instruments.append(instrument)
    
    return instruments 