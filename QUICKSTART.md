# Quick Start Guide

## 🚀 Getting Started

Your Interest Rate Curve Builder is now ready to use! Here's how to get started:

### 1. Command Line Demo
```bash
python3 main.py --demo
```
This runs a demonstration showing:
- Creating sample interest rate swaps
- Building a yield curve from market instruments
- Pricing instruments using the curve
- Calculating key metrics (DV01, convexity, forward rates)

### 2. Web Interface
```bash
python3 main.py --streamlit
```
This launches a beautiful web interface with:
- **Dashboard**: Overview of current curve and key metrics
- **Curve Builder**: Build curves from instruments, swap rates, or manual input
- **Instrument Pricing**: Price swaps and futures with sensitivity analysis
- **Analysis**: Detailed curve analysis and comparisons
- **Data Management**: Import/export curve data

### 3. Run Tests
```bash
python3 main.py --test
```

## 📊 What You Can Do

### Build Curves From:
- **Interest Rate Swaps**: Par swaps with different tenors
- **Interest Rate Futures**: Eurodollar-style futures
- **Swap Rates**: Direct input of market swap rates
- **Manual Input**: Custom curve points

### Price Instruments:
- **Interest Rate Swaps**: Fixed vs floating rate swaps
- **Interest Rate Futures**: Forward rate contracts
- **Sensitivity Analysis**: DV01, convexity, price vs rate shifts

### Analyze Curves:
- **Zero-coupon rates**: Interpolated yield curve
- **Forward rates**: Implied forward rate calculations
- **Discount factors**: Present value calculations
- **Curve metrics**: Slope, key rate durations

## 🏗️ Project Structure

```
curveBuilder/
├── src/
│   ├── core/
│   │   ├── curve.py          # Yield curve implementation
│   │   ├── instruments.py     # IR swaps and futures
│   │   └── bootstrapping.py   # Curve building algorithms
│   ├── utils/
│   │   ├── market_data.py     # Sample data and utilities
│   │   └── visualization.py   # Plotting functions
│   └── ui/
│       └── streamlit_app.py   # Web interface
├── tests/
├── data/
├── main.py                    # Entry point
└── requirements.txt
```

## 💡 Example Usage

### Python API
```python
from src.core.curve import YieldCurve
from src.core.instruments import IRSwap, IRFuture
from src.core.bootstrapping import CurveBootstrapper

# Build curve from instruments
instruments = [IRSwap(0, 5, 0.035), IRFuture(0, 0.25)]
market_prices = [0.0, 99.75]
bootstrapper = CurveBootstrapper()
curve = bootstrapper.bootstrap_curve(instruments, market_prices)

# Price instruments
swap = IRSwap(0, 5, 0.035)
price = swap.price(curve)
dv01 = swap.get_dv01(curve)

# Get curve metrics
rate_5y = curve.get_rate(5.0)
forward_rate = curve.get_forward_rate(1.0, 2.0)
```

## 🎯 Key Features

- **Multiple Interpolation Methods**: Linear, cubic, log-linear
- **Robust Bootstrapping**: Handles various instrument types
- **Sensitivity Analysis**: DV01, convexity calculations
- **Interactive Visualization**: Plotly-based charts
- **Web Interface**: Streamlit dashboard
- **Extensible**: Easy to add new instruments

## 🔧 Customization

### Add New Instruments
Extend the `Instrument` base class in `src/core/instruments.py`

### Add New Interpolation Methods
Modify the `_create_interpolator` method in `src/core/curve.py`

### Custom Market Data
Use the utilities in `src/utils/market_data.py` to load your own data

## 📈 Next Steps

1. **Try the demo**: `python3 main.py --demo`
2. **Launch the web interface**: `python3 main.py --streamlit`
3. **Explore the code**: Check out the core modules
4. **Add your data**: Import your market instruments
5. **Extend functionality**: Add new instruments or analysis tools

Happy curve building! 📈 