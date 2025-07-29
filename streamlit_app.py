"""
Streamlit web interface for the Interest Rate Curve Builder.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import our modules
from src.core.curve import YieldCurve
from src.core.instruments import IRSwap, IRFuture, Instrument
from src.core.bootstrapping import CurveBootstrapper
from src.utils.market_data import (
    load_sample_data, create_sample_instruments, create_sample_futures,
    create_mixed_instruments, get_sample_market_prices, save_sample_data_to_csv
)
from src.utils.visualization import (
    plot_curve, plot_instruments, plot_curve_comparison,
    plot_sensitivity_analysis, create_dashboard_data
)


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Interest Rate Curve Builder",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("📈 Interest Rate Curve Builder")
    st.markdown("Build and analyze yield curves from interest rate futures and swaps")
    
    # Sidebar navigation
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["🏠 Dashboard", "🔧 Curve Builder", "💰 Instrument Pricing", "📊 Analysis", "📁 Data Management"]
    )
    
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🔧 Curve Builder":
        show_curve_builder()
    elif page == "💰 Instrument Pricing":
        show_instrument_pricing()
    elif page == "📊 Analysis":
        show_analysis()
    elif page == "📁 Data Management":
        show_data_management()


def show_dashboard():
    """Show the main dashboard."""
    st.header("🏠 Dashboard")
    
    # Create sample curve for demonstration
    sample_data = load_sample_data()
    instruments = create_sample_instruments()
    market_prices = [0.0] * len(instruments)  # Par swaps
    
    bootstrapper = CurveBootstrapper()
    curve = bootstrapper.bootstrap_curve(instruments, market_prices)
    
    # Get dashboard data
    dashboard_data = create_dashboard_data(curve)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("3M Rate", f"{dashboard_data['short_rate']:.2f}%")
    
    with col2:
        st.metric("10Y Rate", f"{dashboard_data['long_rate']:.2f}%")
    
    with col3:
        st.metric("Curve Slope", f"{dashboard_data['slope']:.2f}%")
    
    with col4:
        st.metric("1Y Forward", f"{dashboard_data['forward_1y']:.2f}%")
    
    # Curve plot
    st.subheader("Current Yield Curve")
    fig = plot_curve(curve, "Sample Yield Curve", show_discount_factors=True)
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("Recent Activity")
    st.info("No recent activity. Start by building a curve or pricing instruments!")


def show_curve_builder():
    """Show the curve building interface."""
    st.header("🔧 Curve Builder")
    
    # Method selection
    method = st.selectbox(
        "Choose curve building method:",
        ["From Market Instruments", "From Swap Rates", "Manual Input"]
    )
    
    if method == "From Market Instruments":
        show_instrument_based_builder()
    elif method == "From Swap Rates":
        show_swap_based_builder()
    elif method == "Manual Input":
        show_manual_curve_builder()


def show_instrument_based_builder():
    """Show instrument-based curve builder."""
    st.subheader("Build Curve from Market Instruments")
    
    # Sample data
    if st.button("Load Sample Data"):
        instruments = create_mixed_instruments()
        market_prices = get_sample_market_prices()
        
        st.session_state.instruments = instruments
        st.session_state.market_prices = market_prices
    
    # Manual input
    st.subheader("Add Instruments")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        instrument_type = st.selectbox("Instrument Type", ["swap", "future"])
    
    with col2:
        tenor = st.number_input("Tenor (years)", min_value=0.1, max_value=30.0, value=1.0, step=0.1)
    
    with col3:
        if instrument_type == "swap":
            rate = st.number_input("Rate (%)", min_value=0.0, max_value=20.0, value=3.0, step=0.1) / 100
        else:
            price = st.number_input("Future Price", min_value=0.0, max_value=100.0, value=99.0, step=0.1)
    
    with col4:
        notional = st.number_input("Notional", min_value=0.1, value=1.0, step=0.1)
    
    if st.button("Add Instrument"):
        if 'instruments' not in st.session_state:
            st.session_state.instruments = []
            st.session_state.market_prices = []
        
        if instrument_type == "swap":
            instrument = IRSwap(0.0, tenor, rate, notional=notional)
            market_price = 0.0  # Par swap
        else:
            instrument = IRFuture(0.0, tenor, notional=notional)
            market_price = price
        
        st.session_state.instruments.append(instrument)
        st.session_state.market_prices.append(market_price)
        
        st.success(f"Added {instrument_type} with tenor {tenor}Y")
    
    # Display current instruments
    if 'instruments' in st.session_state and st.session_state.instruments:
        st.subheader("Current Instruments")
        
        data = []
        for i, (instrument, price) in enumerate(zip(st.session_state.instruments, st.session_state.market_prices)):
            data.append({
                'Index': i,
                'Type': type(instrument).__name__,
                'Tenor': f"{instrument.maturity:.1f}Y",
                'Rate/Price': f"{price:.4f}",
                'Notional': instrument.notional
            })
        
        df = pd.DataFrame(data)
        st.dataframe(df)
        
        # Build curve button
        if st.button("Build Curve"):
            with st.spinner("Building curve..."):
                bootstrapper = CurveBootstrapper()
                curve = bootstrapper.bootstrap_curve(
                    st.session_state.instruments,
                    st.session_state.market_prices
                )
                
                st.session_state.current_curve = curve
                st.success("Curve built successfully!")
                
                # Show curve
                fig = plot_curve(curve, "Bootstrapped Yield Curve")
                st.plotly_chart(fig, use_container_width=True)


def show_swap_based_builder():
    """Show swap-based curve builder."""
    st.subheader("Build Curve from Swap Rates")
    
    # Sample swap rates
    sample_tenors = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
    sample_rates = [2.5, 2.75, 3.0, 3.25, 3.5, 3.75]
    
    # Input swap rates
    st.write("Enter swap rates:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tenors_input = st.text_area(
            "Tenors (years, comma-separated)",
            value=", ".join(map(str, sample_tenors)),
            height=100
        )
    
    with col2:
        rates_input = st.text_area(
            "Rates (%) (comma-separated)",
            value=", ".join(map(str, sample_rates)),
            height=100
        )
    
    if st.button("Build Curve from Swaps"):
        try:
            # Parse inputs
            tenors = [float(x.strip()) for x in tenors_input.split(",")]
            rates = [float(x.strip()) / 100 for x in rates_input.split(",")]
            
            if len(tenors) != len(rates):
                st.error("Number of tenors and rates must match!")
                return
            
            # Build curve
            bootstrapper = CurveBootstrapper()
            curve = bootstrapper.bootstrap_from_swaps(rates, tenors)
            
            st.session_state.current_curve = curve
            st.success("Curve built successfully!")
            
            # Show curve
            fig = plot_curve(curve, "Swap-Based Yield Curve")
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error building curve: {str(e)}")


def show_manual_curve_builder():
    """Show manual curve builder."""
    st.subheader("Manual Curve Input")
    
    # Input curve points
    st.write("Enter curve points manually:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        tenors_input = st.text_area(
            "Tenors (years, comma-separated)",
            value="0.5, 1.0, 2.0, 3.0, 5.0, 10.0",
            height=100
        )
    
    with col2:
        rates_input = st.text_area(
            "Rates (%) (comma-separated)",
            value="2.5, 2.75, 3.0, 3.25, 3.5, 3.75",
            height=100
        )
    
    interpolation_method = st.selectbox(
        "Interpolation Method",
        ["cubic", "linear", "log_linear", "flat", "hybrid"],
        help="Hybrid allows different methods before/after a cutoff date"
    )
    
    # Additional parameters for hybrid interpolation
    cutoff_tenor = None
    pre_cutoff_method = 'flat'
    post_cutoff_method = 'cubic'
    
    if interpolation_method == "hybrid":
        st.subheader("Hybrid Interpolation Settings")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cutoff_tenor = st.number_input(
                "Cutoff Tenor (years)",
                min_value=0.1,
                max_value=50.0,
                value=2.0,
                step=0.25,
                help="Tenor where interpolation method changes"
            )
        
        with col2:
            pre_cutoff_method = st.selectbox(
                "Pre-Cutoff Method",
                ["flat", "linear", "cubic", "log_linear"],
                index=0,
                help="Method for tenors ≤ cutoff"
            )
        
        with col3:
            post_cutoff_method = st.selectbox(
                "Post-Cutoff Method", 
                ["cubic", "linear", "flat", "log_linear"],
                index=0,
                help="Method for tenors > cutoff"
            )
    
    # Show interpolation method explanation
    if interpolation_method == "flat":
        st.info("""
        **Flat Interpolation**: Rates stay constant between known points (step function).
        
        **Best for:**
        • SOFR curve construction
        • Fed Fund rate curves  
        • Central bank policy rates
        • Short-term funding curves
        • Overnight Index Swap (OIS) curves
        
        **Example**: If FOMC sets 5.00% at 3M and 5.25% at 6M, 
        all rates between 3M-6M will be exactly 5.00%.
        """)
    elif interpolation_method == "log_linear":
        st.info("**Log-Linear**: Interpolates log discount factors. Guarantees positive rates and preserves no-arbitrage conditions.")
    elif interpolation_method == "cubic":
        st.info("**Cubic**: Smooth curves using cubic splines. Good for general yield curve construction.")
    elif interpolation_method == "linear":
        st.info("**Linear**: Simple linear interpolation. Fast but may produce unrealistic results.")
    elif interpolation_method == "hybrid":
        st.info(f"""
        **Hybrid Interpolation**: Uses **{pre_cutoff_method}** for tenors ≤ {cutoff_tenor}Y, then **{post_cutoff_method}** for tenors > {cutoff_tenor}Y.
        
        **Perfect for:**
        • SOFR + Swap curves (flat for short rates, smooth for long rates)
        • Central bank policy + market rates
        • Different market segments with different behaviors
        
        **Example**: Flat rates for 0-2Y (FOMC policy), cubic splines for 2Y+ (swap market).
        """)
    
    if st.button("Create Curve"):
        try:
            # Parse inputs
            tenors = [float(x.strip()) for x in tenors_input.split(",")]
            rates = [float(x.strip()) / 100 for x in rates_input.split(",")]
            
            if len(tenors) != len(rates):
                st.error("Number of tenors and rates must match!")
                return
            
            # Create curve
            if interpolation_method == "hybrid":
                curve = YieldCurve(tenors, rates, interpolation_method,
                                 cutoff_tenor=cutoff_tenor,
                                 pre_cutoff_method=pre_cutoff_method,
                                 post_cutoff_method=post_cutoff_method)
            else:
                curve = YieldCurve(tenors, rates, interpolation_method)
            
            st.session_state.current_curve = curve
            st.success("Curve created successfully!")
            
            # Show curve
            fig = plot_curve(curve, "Manual Yield Curve")
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating curve: {str(e)}")


def show_instrument_pricing():
    """Show instrument pricing interface."""
    st.header("💰 Instrument Pricing")
    
    if 'current_curve' not in st.session_state:
        st.warning("Please build a curve first!")
        return
    
    curve = st.session_state.current_curve
    
    # Instrument type selection
    instrument_type = st.selectbox(
        "Choose instrument type:",
        ["Interest Rate Swap", "Interest Rate Future"]
    )
    
    if instrument_type == "Interest Rate Swap":
        show_swap_pricing(curve)
    else:
        show_future_pricing(curve)


def show_swap_pricing(curve):
    """Show swap pricing interface."""
    st.subheader("Interest Rate Swap Pricing")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.number_input("Start Date (years)", min_value=0.0, value=0.0, step=0.1)
        maturity = st.number_input("Maturity (years)", min_value=0.1, value=5.0, step=0.1)
    
    with col2:
        fixed_rate = st.number_input("Fixed Rate (%)", min_value=0.0, max_value=20.0, value=3.5, step=0.1) / 100
        frequency = st.selectbox("Frequency", [1, 2, 4, 12], index=1)
    
    with col3:
        notional = st.number_input("Notional", min_value=0.1, value=1.0, step=0.1)
    
    if st.button("Price Swap"):
        try:
            swap = IRSwap(start_date, maturity, fixed_rate, frequency, notional)
            
            # Calculate price and metrics
            price = swap.price(curve)
            dv01 = swap.get_dv01(curve)
            convexity = swap.get_convexity(curve)
            
            # Display results
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Swap Value", f"{price:.6f}")
            
            with col2:
                st.metric("DV01", f"{dv01:.6f}")
            
            with col3:
                st.metric("Convexity", f"{convexity:.6f}")
            
            # Show cashflows
            cashflows = swap.get_cashflows(curve)
            
            st.subheader("Cashflows")
            cf_df = pd.DataFrame({
                'Date': cashflows['dates'],
                'Fixed': [f"{cf:.6f}" for cf in cashflows['fixed']],
                'Floating': [f"{cf:.6f}" for cf in cashflows['floating']]
            })
            st.dataframe(cf_df)
            
        except Exception as e:
            st.error(f"Error pricing swap: {str(e)}")


def show_future_pricing(curve):
    """Show future pricing interface."""
    st.subheader("Interest Rate Future Pricing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.number_input("Start Date (years)", min_value=0.0, value=0.0, step=0.1)
        maturity = st.number_input("Maturity (years)", min_value=0.1, value=0.25, step=0.1)
    
    with col2:
        notional = st.number_input("Notional", min_value=0.1, value=1.0, step=0.1)
        contract_size = st.number_input("Contract Size", min_value=0.1, value=1.0, step=0.1)
    
    if st.button("Price Future"):
        try:
            future = IRFuture(start_date, maturity, notional, contract_size)
            
            # Calculate price and metrics
            price = future.price(curve)
            dv01 = future.get_dv01(curve)
            convexity = future.get_convexity(curve)
            
            # Display results
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Future Price", f"{price:.6f}")
            
            with col2:
                st.metric("DV01", f"{dv01:.6f}")
            
            with col3:
                st.metric("Convexity", f"{convexity:.6f}")
            
            # Show implied rate
            forward_rate = curve.get_forward_rate(start_date, maturity)
            st.info(f"Implied Forward Rate: {forward_rate*100:.2f}%")
            
        except Exception as e:
            st.error(f"Error pricing future: {str(e)}")


def show_analysis():
    """Show analysis interface."""
    st.header("📊 Analysis")
    
    if 'current_curve' not in st.session_state:
        st.warning("Please build a curve first!")
        return
    
    curve = st.session_state.current_curve
    
    # Analysis options
    analysis_type = st.selectbox(
        "Choose analysis type:",
        ["Curve Analysis", "Sensitivity Analysis", "Curve Comparison"]
    )
    
    if analysis_type == "Curve Analysis":
        show_curve_analysis(curve)
    elif analysis_type == "Sensitivity Analysis":
        show_sensitivity_analysis(curve)
    else:
        show_curve_comparison(curve)


def show_curve_analysis(curve):
    """Show curve analysis."""
    st.subheader("Curve Analysis")
    
    # Key metrics
    dashboard_data = create_dashboard_data(curve)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Key Metrics:**")
        st.write(f"- 3M Rate: {dashboard_data['short_rate']:.2f}%")
        st.write(f"- 10Y Rate: {dashboard_data['long_rate']:.2f}%")
        st.write(f"- Curve Slope: {dashboard_data['slope']:.2f}%")
        st.write(f"- 1Y Forward: {dashboard_data['forward_1y']:.2f}%")
    
    with col2:
        st.write("**Discount Factors:**")
        st.write(f"- 1Y: {dashboard_data['df_1y']:.4f}")
        st.write(f"- 5Y: {dashboard_data['df_5y']:.4f}")
        st.write(f"- 10Y: {dashboard_data['df_10y']:.4f}")
    
    # Detailed curve plot
    fig = plot_curve(curve, "Detailed Curve Analysis", show_discount_factors=True, show_forward_rates=True)
    st.plotly_chart(fig, use_container_width=True)


def show_sensitivity_analysis(curve):
    """Show sensitivity analysis."""
    st.subheader("Sensitivity Analysis")
    
    # Create sample instrument
    swap = IRSwap(0.0, 5.0, 0.035, notional=1.0)
    
    # Analysis parameters
    col1, col2 = st.columns(2)
    
    with col1:
        min_shift = st.number_input("Min Shift (bp)", value=-50, step=5)
        max_shift = st.number_input("Max Shift (bp)", value=50, step=5)
        step = st.number_input("Step (bp)", value=5, step=1)
    
    with col2:
        instrument_type = st.selectbox("Instrument", ["5Y Swap", "3M Future"])
        
        if instrument_type == "5Y Swap":
            instrument = swap
        else:
            instrument = IRFuture(0.0, 0.25, notional=1.0)
    
    if st.button("Run Sensitivity Analysis"):
        shifts = list(range(min_shift, max_shift + 1, step))
        fig = plot_sensitivity_analysis(instrument, curve, shifts)
        st.plotly_chart(fig, use_container_width=True)


def show_curve_comparison(curve):
    """Show curve comparison."""
    st.subheader("Curve Comparison")
    
    # Create comparison curves
    flat_curve = YieldCurve(curve.tenors, [0.03] * len(curve.tenors))
    steep_curve = YieldCurve(curve.tenors, [0.02 + 0.01 * t for t in curve.tenors])
    
    curves = [curve, flat_curve, steep_curve]
    names = ["Current", "Flat 3%", "Steep"]
    
    fig = plot_curve_comparison(curves, names)
    st.plotly_chart(fig, use_container_width=True)


def show_data_management():
    """Show data management interface."""
    st.header("📁 Data Management")
    
    # Export current curve
    if 'current_curve' in st.session_state:
        st.subheader("Export Curve")
        
        curve = st.session_state.current_curve
        curve_df = curve.to_dataframe()
        
        # Download button
        csv = curve_df.to_csv(index=False)
        st.download_button(
            label="Download Curve Data",
            data=csv,
            file_name="yield_curve.csv",
            mime="text/csv"
        )
        
        st.dataframe(curve_df)
    
    # Import data
    st.subheader("Import Market Data")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            data = pd.read_csv(uploaded_file)
            st.write("Uploaded data:")
            st.dataframe(data)
            
            if st.button("Create Instruments from Data"):
                st.info("Data import functionality to be implemented")
                
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
    
    # Sample data
    st.subheader("Sample Data")
    
    if st.button("Generate Sample Data"):
        save_sample_data_to_csv()
        st.success("Sample data saved to data/sample_data.csv")


if __name__ == "__main__":
    main() 