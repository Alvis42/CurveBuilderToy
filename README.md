# Interest Rate Curve Builder

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-black.svg)](https://github.com/psf/black)

A comprehensive tool for building and calibrating interest rate curves from market instruments including interest rate futures and interest rate swaps.

## 🌟 Features

- **Curve Building**: Bootstrap yield curves from market instruments
- **Instrument Pricing**: Price interest rate futures and swaps
- **Interactive UI**: Streamlit-based interface for curve management
- **Visualization**: Plot curves and analyze sensitivities
- **Market Data**: Handle real market data formats
- **Clean Code**: Follows SOLID principles and clean code practices

## 🏗️ Project Structure

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

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/interest-rate-curve-builder.git
cd interest-rate-curve-builder

# Install dependencies
pip install -r requirements.txt
```

### Usage

#### Command Line Demo
```bash
python3 main.py --demo
```

#### Web Interface
```bash
python3 main.py --streamlit
```

#### Run Tests
```bash
python3 main.py --test
```

### Python API

```python
from src.core.curve import YieldCurve
from src.core.instruments import IRSwap, IRFuture

# Build curve from market instruments
curve = YieldCurve.from_instruments(instruments, market_prices)

# Price instruments
swap = IRSwap(0.0, 5.0, 0.035)
price = swap.price(curve)
dv01 = swap.get_dv01(curve)
```

## 📊 Core Components

### 1. Yield Curve (`src/core/curve.py`)
- Zero-coupon yield curve representation
- Interpolation methods (linear, cubic, log-linear)
- Forward rate calculations
- Discount factor computations

### 2. Instruments (`src/core/instruments.py`)
- Interest Rate Swap pricing
- Interest Rate Future pricing
- Sensitivity calculations (DV01, convexity)
- Cashflow analysis

### 3. Bootstrapping (`src/core/bootstrapping.py`)
- Iterative curve building from market prices
- Error minimization algorithms
- Curve smoothing techniques

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

## 📈 Screenshots

### Dashboard
![Dashboard](docs/dashboard.png)

### Curve Builder
![Curve Builder](docs/curve_builder.png)

### Instrument Pricing
![Pricing](docs/pricing.png)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the web interface
- Uses [Plotly](https://plotly.com/) for interactive visualizations
- Implements clean code principles and SOLID design patterns

## 📞 Support

If you have any questions or need help, please open an issue on GitHub.

---

**Happy curve building! 📈**