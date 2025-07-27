# Interest Rate Curve Builder

A comprehensive tool for building and calibrating interest rate curves from market instruments including interest rate futures and interest rate swaps.

## Features

- **Curve Building**: Bootstrap yield curves from market instruments
- **Instrument Pricing**: Price interest rate futures and swaps
- **Interactive UI**: Streamlit-based interface for curve management
- **Visualization**: Plot curves and analyze sensitivities
- **Market Data**: Handle real market data formats

## Project Structure

```
curveBuilder/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── curve.py          # Core curve building logic
│   │   ├── instruments.py     # IR futures and swaps pricing
│   │   └── bootstrapping.py   # Curve bootstrapping algorithms
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── market_data.py     # Market data handling
│   │   └── visualization.py   # Plotting utilities
│   └── ui/
│       ├── __init__.py
│       └── streamlit_app.py   # Streamlit web interface
├── tests/
│   └── test_curve.py
├── data/
│   └── sample_data.csv
├── requirements.txt
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Command Line
```bash
python -m src.ui.streamlit_app
```

### Python API
```python
from src.core.curve import YieldCurve
from src.core.instruments import IRSwap, IRFuture

# Build curve from market instruments
curve = YieldCurve.from_instruments(instruments, market_prices)
```

## Core Components

### 1. Yield Curve (`src/core/curve.py`)
- Zero-coupon yield curve representation
- Interpolation methods (linear, cubic spline)
- Forward rate calculations

### 2. Instruments (`src/core/instruments.py`)
- Interest Rate Swap pricing
- Interest Rate Future pricing
- Sensitivity calculations (DV01, convexity)

### 3. Bootstrapping (`src/core/bootstrapping.py`)
- Iterative curve building from market prices
- Error minimization algorithms
- Curve smoothing techniques

## License

MIT License 