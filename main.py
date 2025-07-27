#!/usr/bin/env python3
"""
Main entry point for the Interest Rate Curve Builder.
"""

import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.curve import YieldCurve
from src.core.instruments import IRSwap, IRFuture
from src.core.bootstrapping import CurveBootstrapper
from src.utils.market_data import create_sample_instruments, get_sample_market_prices
from src.utils.visualization import plot_curve


def run_streamlit():
    """Run the Streamlit web interface."""
    import subprocess
    import sys
    
    # Run streamlit app
    cmd = [sys.executable, "-m", "streamlit", "run", "streamlit_app.py"]
    subprocess.run(cmd)


def run_demo():
    """Run a command-line demo."""
    print("📈 Interest Rate Curve Builder Demo")
    print("=" * 50)
    
    # Create sample instruments
    instruments = create_sample_instruments()
    market_prices = [0.0] * len(instruments)  # Par swaps have zero market price
    
    print(f"Created {len(instruments)} sample instruments:")
    for i, instrument in enumerate(instruments):
        print(f"  {i+1}. {instrument}")
    
    # Build curve
    print("\n🔧 Building yield curve...")
    bootstrapper = CurveBootstrapper()
    curve = bootstrapper.bootstrap_curve(instruments, market_prices)
    
    print(f"✅ Curve built successfully!")
    print(f"   Tenors: {curve.tenors}")
    print(f"   Rates: {[f'{r*100:.2f}%' for r in curve.rates]}")
    
    # Price some instruments
    print("\n💰 Pricing instruments...")
    
    # Price a 5Y swap
    swap = IRSwap(0.0, 5.0, 0.035, notional=1.0)
    swap_price = swap.price(curve)
    swap_dv01 = swap.get_dv01(curve)
    
    print(f"   5Y Swap (3.5% fixed):")
    print(f"     Price: {swap_price:.6f}")
    print(f"     DV01: {swap_dv01:.6f}")
    
    # Price a 3M future
    future = IRFuture(0.0, 0.25, notional=1.0)
    future_price = future.price(curve)
    future_dv01 = future.get_dv01(curve)
    
    print(f"   3M Future:")
    print(f"     Price: {future_price:.6f}")
    print(f"     DV01: {future_dv01:.6f}")
    
    # Show some curve metrics
    print("\n📊 Curve Analysis:")
    short_rate = curve.get_rate(0.25) * 100
    long_rate = curve.get_rate(10.0) * 100
    slope = long_rate - short_rate
    
    print(f"   3M Rate: {short_rate:.2f}%")
    print(f"   10Y Rate: {long_rate:.2f}%")
    print(f"   Curve Slope: {slope:.2f}%")
    
    # Forward rates
    forward_1y = curve.get_forward_rate(0.0, 1.0) * 100
    forward_2y = curve.get_forward_rate(1.0, 2.0) * 100
    
    print(f"   1Y Forward: {forward_1y:.2f}%")
    print(f"   2Y Forward: {forward_2y:.2f}%")
    
    print("\n🎉 Demo completed successfully!")
    print("Run 'python main.py --streamlit' to launch the web interface.")


def run_tests():
    """Run the test suite."""
    import subprocess
    import sys
    
    print("🧪 Running tests...")
    cmd = [sys.executable, "-m", "unittest", "discover", "tests"]
    subprocess.run(cmd)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Interest Rate Curve Builder")
    parser.add_argument(
        "--streamlit", 
        action="store_true", 
        help="Launch Streamlit web interface"
    )
    parser.add_argument(
        "--demo", 
        action="store_true", 
        help="Run command-line demo"
    )
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="Run tests"
    )
    
    args = parser.parse_args()
    
    if args.streamlit:
        run_streamlit()
    elif args.demo:
        run_demo()
    elif args.test:
        run_tests()
    else:
        # Default to demo
        run_demo()


if __name__ == "__main__":
    main() 