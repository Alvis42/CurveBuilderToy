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
        ["🏠 Dashboard", "🔧 Curve Builder", "💰 Instrument Pricing", "📊 Analysis", "🔄 Forward Swaps", "📁 Data Management"]
    )
    
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🔧 Curve Builder":
        show_curve_builder()
    elif page == "💰 Instrument Pricing":
        show_instrument_pricing()
    elif page == "📊 Analysis":
        show_analysis()
    elif page == "🔄 Forward Swaps":
        show_forward_swaps()
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


def show_forward_swaps():
    """Show the forward starting swaps interface."""
    st.header("🔄 Forward Starting Swaps")
    st.markdown("Analyze and build curves with forward starting swaps that control specific curve segments")
    
    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Interactive Builder", 
        "🔍 Overlap Analysis", 
        "🎯 Par Rate Calculator",
        "📈 Sensitivity Analysis"
    ])
    
    with tab1:
        show_forward_swap_builder()
    
    with tab2:
        show_overlap_analysis()
    
    with tab3:
        show_par_rate_calculator()
    
    with tab4:
        show_forward_sensitivity_analysis()


def show_forward_swap_builder():
    """Interactive forward starting swap builder."""
    st.subheader("📊 Forward Starting Swap Builder")
    st.markdown("Build curves using a mix of spot and forward starting swaps")
    
    # Initialize session state for instruments
    if 'forward_instruments' not in st.session_state:
        st.session_state.forward_instruments = []
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**Add Instruments**")
        
        # Instrument type selection
        swap_type = st.radio("Swap Type", ["Spot Starting", "Forward Starting"])
        
        if swap_type == "Spot Starting":
            start_date = 0.0
            maturity = st.number_input("Maturity (years)", min_value=0.25, max_value=30.0, value=5.0, step=0.25)
        else:
            start_date = st.number_input("Start Date (years)", min_value=0.25, max_value=25.0, value=2.0, step=0.25)
            maturity = st.number_input("Maturity (years)", min_value=start_date + 0.25, max_value=30.0, 
                                     value=max(start_date + 3.0, 5.0), step=0.25)
        
        fixed_rate = st.number_input("Fixed Rate (%)", min_value=0.0, max_value=20.0, value=4.0, step=0.1) / 100
        frequency = st.selectbox("Payment Frequency", [1, 2, 4], index=1, 
                                format_func=lambda x: f"{x}x per year ({'Annual' if x==1 else 'Semi-annual' if x==2 else 'Quarterly'})")
        notional = st.number_input("Notional", min_value=1.0, value=1000000.0, step=100000.0)
        
        if st.button("Add Swap"):
            try:
                new_swap = IRSwap(start_date, maturity, fixed_rate, frequency, notional)
                st.session_state.forward_instruments.append(new_swap)
                st.success(f"Added: {new_swap}")
            except ValueError as e:
                st.error(f"Error: {e}")
        
        # Clear all button
        if st.button("Clear All"):
            st.session_state.forward_instruments = []
            st.success("Cleared all instruments")
        
        # Show current instruments
        st.markdown("**Current Instruments:**")
        for i, inst in enumerate(st.session_state.forward_instruments):
            col_inst, col_remove = st.columns([3, 1])
            with col_inst:
                st.text(f"{i+1}. {inst}")
            with col_remove:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.forward_instruments.pop(i)
                    st.rerun()
    
    with col2:
        if len(st.session_state.forward_instruments) > 0:
            # Coverage analysis
            bootstrapper = CurveBootstrapper()
            coverage = bootstrapper.analyze_forward_swap_coverage(st.session_state.forward_instruments)
            
            st.markdown("**📋 Coverage Analysis**")
            st.info(f"""
            - **Total instruments**: {coverage['total_instruments']}
            - **Forward starting**: {coverage['forward_starting_count']}
            - **Spot starting**: {coverage['spot_starting_count']}
            - **Curve range**: {coverage['min_tenor']:.1f}Y - {coverage['max_tenor']:.1f}Y
            """)
            
            # Visualize coverage
            fig = create_coverage_visualization(st.session_state.forward_instruments)
            st.plotly_chart(fig, use_container_width=True, key="builder_coverage_viz")
            
            # Overlap detection
            overlaps = find_overlapping_regions_streamlit(st.session_state.forward_instruments)
            if overlaps:
                st.warning(f"⚠️ Found {len(overlaps)} overlapping regions:")
                for overlap in overlaps:
                    st.write(f"- **{overlap['start']:.1f}Y-{overlap['end']:.1f}Y**: {len(overlap['instruments'])} instruments")
            else:
                st.success("✅ No overlapping regions detected")
            
            # Bootstrap curve
            if st.button("🚀 Bootstrap Curve"):
                market_prices = [0.0] * len(st.session_state.forward_instruments)  # Par swaps
                
                try:
                    with st.spinner("Building curve..."):
                        curve = bootstrapper.bootstrap_with_forward_control(
                            st.session_state.forward_instruments, market_prices
                        )
                    
                    st.success("✅ Curve built successfully!")
                    
                    # Show curve plot
                    fig = plot_curve(curve, "Forward Swap Curve")
                    st.plotly_chart(fig, use_container_width=True, key="forward_swap_curve_plot")
                    
                    # Verification
                    st.markdown("**🔍 Pricing Verification:**")
                    total_error = 0
                    for i, inst in enumerate(st.session_state.forward_instruments):
                        price = inst.price(curve)
                        error = abs(price)
                        total_error += error
                        
                        status = "✅" if error < 0.01 else "⚠️" if error < 0.05 else "❌"
                        st.write(f"{status} {inst}: Price = {price:.6f}, Error = {error:.6f}")
                    
                    avg_error = total_error / len(st.session_state.forward_instruments)
                    st.metric("Average Pricing Error", f"{avg_error:.6f}")
                    
                    if avg_error < 0.01:
                        st.success("🎯 Excellent fit! All instruments price very close to zero.")
                    elif avg_error < 0.05:
                        st.warning("⚠️ Reasonable fit, but some pricing errors exist (typical for overlapping swaps).")
                    else:
                        st.error("❌ Poor fit - consider reviewing instrument setup or checking for inconsistencies.")
                
                except Exception as e:
                    st.error(f"❌ Curve building failed: {e}")
        else:
            st.info("👆 Add some instruments to start building a curve")


def show_overlap_analysis():
    """Show overlap analysis tool."""
    st.subheader("🔍 Overlap Analysis")
    st.markdown("Analyze what happens when forward starting swaps overlap")
    
    # Predefined scenarios
    scenario = st.selectbox(
        "Choose a scenario:",
        ["Custom", "Heavy Overlap", "Clean Partition", "Market Reality", "Gaps Example"]
    )
    
    if scenario == "Heavy Overlap":
        instruments = [
            IRSwap(0.0, 2.0, 0.030),
            IRSwap(0.0, 3.0, 0.035),
            IRSwap(1.0, 3.0, 0.038),
            IRSwap(2.0, 4.0, 0.040),
            IRSwap(1.5, 3.5, 0.039),
        ]
    elif scenario == "Clean Partition":
        instruments = [
            IRSwap(0.0, 2.0, 0.030),
            IRSwap(2.0, 5.0, 0.035),
            IRSwap(5.0, 10.0, 0.040),
        ]
    elif scenario == "Market Reality":
        instruments = [
            IRSwap(0.0, 1.0, 0.025),   # 1Y liquid
            IRSwap(0.0, 2.0, 0.030),   # 2Y liquid
            IRSwap(1.0, 4.0, 0.035),   # 1Y-4Y forward
            IRSwap(2.0, 5.0, 0.040),   # 2Y-5Y forward (slight overlap)
            IRSwap(5.0, 10.0, 0.045),  # 5Y-10Y forward
        ]
    elif scenario == "Gaps Example":
        instruments = [
            IRSwap(0.0, 1.0, 0.025),
            IRSwap(3.0, 5.0, 0.040),
            IRSwap(7.0, 10.0, 0.045),
        ]
    else:  # Custom
        instruments = st.session_state.get('forward_instruments', [])
    
    if instruments:
        bootstrapper = CurveBootstrapper()
        
        # Coverage analysis
        coverage = bootstrapper.analyze_forward_swap_coverage(instruments)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📊 Coverage Summary**")
            st.metric("Total Instruments", coverage['total_instruments'])
            st.metric("Forward Starting", coverage['forward_starting_count'])
            st.metric("Spot Starting", coverage['spot_starting_count'])
            st.metric("Curve Range", f"{coverage['min_tenor']:.1f}Y - {coverage['max_tenor']:.1f}Y")
        
        with col2:
            # Find overlaps
            overlaps = find_overlapping_regions_streamlit(instruments)
            st.markdown("**⚠️ Overlap Detection**")
            
            if overlaps:
                st.error(f"Found {len(overlaps)} overlapping regions")
                for overlap in overlaps:
                    with st.expander(f"Overlap: {overlap['start']:.1f}Y - {overlap['end']:.1f}Y"):
                        st.write(f"**{len(overlap['instruments'])} instruments:**")
                        for inst_str in overlap['instruments']:
                            st.write(f"- {inst_str}")
            else:
                st.success("✅ No overlaps detected")
        
        # Visualization
        fig = create_coverage_visualization(instruments)
        st.plotly_chart(fig, use_container_width=True, key="overlap_analysis_coverage_viz")
        
        # Try to bootstrap and show results
        if st.button("🧪 Test Bootstrapping"):
            market_prices = [0.0] * len(instruments)
            
            try:
                with st.spinner("Testing curve construction..."):
                    curve = bootstrapper.bootstrap_with_forward_control(instruments, market_prices)
                
                st.success("✅ Bootstrapping successful!")
                
                # Calculate and display pricing errors
                st.markdown("**🔍 Pricing Results:**")
                errors = []
                for i, inst in enumerate(instruments):
                    price = inst.price(curve)
                    error = abs(price - market_prices[i])
                    errors.append(error)
                    
                    status = "✅" if error < 0.01 else "⚠️" if error < 0.05 else "❌"
                    st.write(f"{status} {inst}: Price = {price:.6f}, Target = {market_prices[i]:.6f}, Error = {error:.6f}")
                
                total_error = sum(errors)
                avg_error = total_error / len(errors)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Error", f"{total_error:.6f}")
                with col2:
                    st.metric("Average Error", f"{avg_error:.6f}")
                
                # Analysis
                if avg_error < 0.001:
                    st.success("🎯 **Perfect fit!** All instruments price exactly to target.")
                elif avg_error < 0.01:
                    st.success("✅ **Excellent fit!** Very small pricing errors.")
                elif avg_error < 0.05:
                    st.warning("⚠️ **Reasonable fit** - Some errors due to overlaps (normal for over-determined systems).")
                else:
                    st.error("❌ **Poor fit** - Large errors suggest inconsistent instrument pricing or numerical issues.")
                
            except Exception as e:
                st.error(f"❌ Bootstrapping failed: {e}")
                st.info("This might happen with heavily over-determined or inconsistent systems.")
    else:
        st.info("📝 Please select a scenario or add instruments in the Builder tab")


def show_par_rate_calculator():
    """Show par rate calculator for forward swaps."""
    st.subheader("🎯 Par Rate Calculator")
    st.markdown("Calculate fair rates for forward starting swaps given a yield curve")
    
    # Create a base curve
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**📈 Define Base Curve**")
        
        curve_type = st.radio("Curve Type", ["Sample Curve", "Custom Points"])
        
        if curve_type == "Sample Curve":
            curve_shape = st.selectbox("Shape", ["Upward Sloping", "Flat", "Inverted", "Humped"])
            
            if curve_shape == "Upward Sloping":
                tenors = [0.5, 1, 2, 3, 5, 7, 10]
                rates = [0.02, 0.025, 0.03, 0.035, 0.04, 0.042, 0.045]
            elif curve_shape == "Flat":
                tenors = [0.5, 1, 2, 3, 5, 7, 10]
                rates = [0.04] * 7
            elif curve_shape == "Inverted":
                tenors = [0.5, 1, 2, 3, 5, 7, 10]
                rates = [0.05, 0.045, 0.04, 0.035, 0.03, 0.028, 0.025]
            else:  # Humped
                tenors = [0.5, 1, 2, 3, 5, 7, 10]
                rates = [0.02, 0.03, 0.045, 0.05, 0.045, 0.04, 0.038]
            
            curve = YieldCurve(tenors, rates, interpolation_method='cubic')
            
        else:  # Custom
            st.info("Enter custom curve points (tenor, rate)")
            # This could be expanded with dynamic input fields
            curve = None
        
        if curve:
            st.markdown("**🔧 Forward Swap Parameters**")
            start_date = st.number_input("Start Date (years)", min_value=0.0, max_value=25.0, value=2.0, step=0.25)
            maturity = st.number_input("End Date (years)", min_value=start_date + 0.25, max_value=30.0, value=5.0, step=0.25)
            frequency = st.selectbox("Frequency", [1, 2, 4], index=1)
            notional = st.number_input("Notional", value=1000000.0)
    
    with col2:
        if curve:
            # Show the base curve
            fig = plot_curve(curve, f"{curve_shape} Yield Curve")
            st.plotly_chart(fig, use_container_width=True, key="par_rate_base_curve")
            
            # Calculate par rates for different forward swaps
            if st.button("Calculate Par Rates"):
                st.markdown("**📊 Par Rate Results**")
                
                # Test various forward swap periods
                test_swaps = [
                    (0.0, 1.0, "1Y Spot"),
                    (0.0, 2.0, "2Y Spot"),
                    (0.0, 5.0, "5Y Spot"),
                    (1.0, 3.0, "1Y-3Y Forward"),
                    (2.0, 5.0, "2Y-5Y Forward"),
                    (3.0, 7.0, "3Y-7Y Forward"),
                    (5.0, 10.0, "5Y-10Y Forward"),
                ]
                
                results = []
                for start, end, description in test_swaps:
                    try:
                        swap = IRSwap(start, end, 0.04, frequency, notional)  # Rate will be replaced
                        par_rate = swap.get_par_rate(curve)
                        results.append({
                            "Swap": description,
                            "Period": f"{start}Y - {end}Y",
                            "Par Rate": f"{par_rate:.4%}",
                            "Rate (bp)": f"{par_rate*10000:.1f}"
                        })
                    except Exception as e:
                        results.append({
                            "Swap": description,
                            "Period": f"{start}Y - {end}Y",
                            "Par Rate": "Error",
                            "Rate (bp)": str(e)[:30]
                        })
                
                # Display results
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)
                
                # Specific swap calculation
                if start_date < maturity:
                    try:
                        specific_swap = IRSwap(start_date, maturity, 0.04, frequency, notional)
                        specific_par_rate = specific_swap.get_par_rate(curve)
                        
                        st.success(f"**🎯 Your Forward Swap ({start_date}Y-{maturity}Y)**")
                        st.metric("Par Rate", f"{specific_par_rate:.4%}")
                        st.metric("Rate (basis points)", f"{specific_par_rate*10000:.1f} bp")
                        
                        # Create swap at par rate and verify pricing
                        par_swap = IRSwap(start_date, maturity, specific_par_rate, frequency, notional)
                        verification_price = par_swap.price(curve)
                        
                        if abs(verification_price) < 0.0001:
                            st.success(f"✅ Verification: Swap prices to {verification_price:.8f} (≈ 0)")
                        else:
                            st.warning(f"⚠️ Verification: Small pricing error {verification_price:.8f}")
                            
                    except Exception as e:
                        st.error(f"Error calculating par rate: {e}")
        else:
            st.info("👈 Define a base curve to calculate par rates")


def show_forward_sensitivity_analysis():
    """Show sensitivity analysis for forward starting swaps."""
    st.subheader("📈 Forward Swap Sensitivity Analysis")
    st.markdown("Analyze how forward starting swaps respond to rate changes in different curve segments")
    
    # Create base curve and swaps
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**📊 Setup**")
        
        # Base curve
        tenors = [1.0, 2.0, 3.0, 5.0, 7.0, 10.0]
        rates = [0.025, 0.03, 0.035, 0.04, 0.042, 0.045]
        curve = YieldCurve(tenors, rates, interpolation_method='cubic')
        
        # Swaps to analyze
        swaps = [
            IRSwap(1.0, 4.0, 0.035, 2, 1000000),    # 1Y-4Y forward
            IRSwap(2.0, 5.0, 0.040, 2, 1000000),    # 2Y-5Y forward  
            IRSwap(3.0, 7.0, 0.042, 2, 1000000),    # 3Y-7Y forward
        ]
        
        st.info(f"""
        **Base Curve**: Upward sloping from 2.5% to 4.5%
        
        **Test Swaps**:
        - 1Y-4Y Forward Swap
        - 2Y-5Y Forward Swap  
        - 3Y-7Y Forward Swap
        """)
        
        # Rate shock settings
        shock_size = st.slider("Rate Shock (basis points)", 1, 100, 10)
        shock_bp = shock_size / 10000
        
        # Segment selection
        segments = [(1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 5.0), (5.0, 7.0)]
        selected_segment = st.selectbox(
            "Focus on segment:",
            segments,
            format_func=lambda x: f"{x[0]}Y - {x[1]}Y"
        )
    
    with col2:
        if st.button("🔍 Run Sensitivity Analysis"):
            st.markdown("**📊 Sensitivity Results**")
            
            # Create results table
            results = []
            
            for swap in swaps:
                row = {"Swap": str(swap)}
                
                for start_seg, end_seg in segments:
                    # Calculate analytical sensitivity
                    sensitivity = swap.get_forward_rate_sensitivity(curve, start_seg, end_seg)
                    
                    # Determine if this segment affects the swap
                    swap_start, swap_end = swap.forward_tenor_range
                    if start_seg >= swap_start and end_seg <= swap_end:
                        impact = "Direct"
                    elif end_seg <= swap_start or start_seg >= swap_end:
                        impact = "None"
                    else:
                        impact = "Partial"
                    
                    row[f"{start_seg}-{end_seg}Y"] = {
                        "analytical": sensitivity,
                        "impact": impact
                    }
                
                results.append(row)
            
            # Display sensitivity matrix
            st.markdown("**Analytical Sensitivity (per 1bp rate change)**")
            
            # Create DataFrame for display
            display_data = []
            for result in results:
                row_data = {"Swap": result["Swap"]}
                for start_seg, end_seg in segments:
                    key = f"{start_seg}-{end_seg}Y"
                    sensitivity = result[key]["analytical"]
                    impact = result[key]["impact"]
                    
                    if impact == "Direct":
                        cell_value = f"{sensitivity:.6f} ✓"
                    elif impact == "None":
                        cell_value = f"{sensitivity:.6f} ✗"
                    else:
                        cell_value = f"{sensitivity:.6f} ~"
                    
                    row_data[key] = cell_value
                
                display_data.append(row_data)
            
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True)
            
            st.markdown("""
            **Legend:**
            - ✓ Direct impact (segment within swap period)
            - ✗ No impact (segment outside swap period)  
            - ~ Partial impact (segment partially overlaps)
            """)
            
            # Focused analysis on selected segment
            st.markdown(f"**🔍 Focus: {selected_segment[0]}Y-{selected_segment[1]}Y Segment**")
            
            focused_results = []
            for swap in swaps:
                start_seg, end_seg = selected_segment
                sensitivity = swap.get_forward_rate_sensitivity(curve, start_seg, end_seg)
                swap_start, swap_end = swap.forward_tenor_range
                
                if start_seg >= swap_start and end_seg <= swap_end:
                    explanation = f"✅ Fully within swap period ({swap_start}Y-{swap_end}Y)"
                elif end_seg <= swap_start or start_seg >= swap_end:
                    explanation = f"❌ Outside swap period ({swap_start}Y-{swap_end}Y)"
                else:
                    explanation = f"⚠️ Partially overlaps with swap period ({swap_start}Y-{swap_end}Y)"
                
                focused_results.append({
                    "Swap": str(swap),
                    "Sensitivity": f"{sensitivity:.6f}",
                    "Explanation": explanation
                })
            
            focused_df = pd.DataFrame(focused_results)
            st.dataframe(focused_df, use_container_width=True)


def create_coverage_visualization(instruments):
    """Create a Plotly visualization of instrument coverage."""
    fig = go.Figure()
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF']
    
    for i, instrument in enumerate(instruments):
        start = instrument.start_date
        end = instrument.maturity
        
        # Add horizontal bar for coverage
        fig.add_trace(go.Scatter(
            x=[start, end, end, start, start],
            y=[i, i, i+0.8, i+0.8, i],
            fill="toself",
            fillcolor=colors[i % len(colors)],
            line=dict(color=colors[i % len(colors)], width=2),
            name=str(instrument),
            text=f"{start}Y-{end}Y",
            textposition="middle center",
            mode="lines+text"
        ))
    
    # Update layout
    fig.update_layout(
        title="Forward Starting Swap Coverage",
        xaxis_title="Tenor (Years)",
        yaxis_title="Instruments",
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(len(instruments))),
            ticktext=[f"Swap {i+1}" for i in range(len(instruments))]
        ),
        height=max(400, len(instruments) * 60),
        showlegend=False
    )
    
    return fig


def find_overlapping_regions_streamlit(instruments):
    """Find overlapping regions for Streamlit display."""
    # Create a list of all tenor breakpoints
    breakpoints = set()
    for inst in instruments:
        breakpoints.add(inst.start_date)
        breakpoints.add(inst.maturity)
    
    breakpoints = sorted(list(breakpoints))
    
    overlaps = []
    for i in range(len(breakpoints) - 1):
        start = breakpoints[i]
        end = breakpoints[i + 1]
        mid_point = (start + end) / 2
        
        # Find instruments that cover this region
        covering_instruments = []
        for inst in instruments:
            if inst.start_date <= mid_point <= inst.maturity:
                covering_instruments.append(str(inst))
        
        if len(covering_instruments) > 1:
            overlaps.append({
                'start': start,
                'end': end,
                'instruments': covering_instruments
            })
    
    return overlaps


if __name__ == "__main__":
    main() 