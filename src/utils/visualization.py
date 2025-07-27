"""
Visualization utilities for yield curves and instruments.
"""

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from typing import List, Optional, Dict, Any
from ..core.curve import YieldCurve
from ..core.instruments import Instrument


def plot_curve(curve: YieldCurve, 
               title: str = "Yield Curve",
               show_discount_factors: bool = False,
               show_forward_rates: bool = False) -> go.Figure:
    """
    Create an interactive plot of the yield curve.
    
    Args:
        curve: YieldCurve object
        title: Plot title
        show_discount_factors: Whether to show discount factors
        show_forward_rates: Whether to show forward rates
        
    Returns:
        Plotly figure object
    """
    # Create subplots
    subplot_titles = ["Zero-Coupon Rates"]
    if show_discount_factors:
        subplot_titles.append("Discount Factors")
    if show_forward_rates:
        subplot_titles.append("Forward Rates")
    
    fig = make_subplots(
        rows=len(subplot_titles), 
        cols=1,
        subplot_titles=subplot_titles,
        vertical_spacing=0.1
    )
    
    # Generate smooth curve for plotting
    tenors_smooth = np.linspace(curve.tenors[0], curve.tenors[-1], 100)
    rates_smooth = [curve.get_rate(t) for t in tenors_smooth]
    
    # Plot zero-coupon rates
    fig.add_trace(
        go.Scatter(
            x=curve.tenors,
            y=curve.rates * 100,  # Convert to percentage
            mode='markers',
            name='Market Points',
            marker=dict(size=8, color='red')
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=tenors_smooth,
            y=np.array(rates_smooth) * 100,
            mode='lines',
            name='Interpolated Curve',
            line=dict(color='blue', width=2)
        ),
        row=1, col=1
    )
    
    current_row = 2
    
    # Plot discount factors if requested
    if show_discount_factors:
        discount_factors = [curve.get_discount_factor(t) for t in tenors_smooth]
        
        fig.add_trace(
            go.Scatter(
                x=tenors_smooth,
                y=discount_factors,
                mode='lines',
                name='Discount Factors',
                line=dict(color='green', width=2)
            ),
            row=current_row, col=1
        )
        current_row += 1
    
    # Plot forward rates if requested
    if show_forward_rates:
        forward_rates = []
        forward_tenors = []
        for i in range(len(tenors_smooth) - 1):
            start_tenor = tenors_smooth[i]
            end_tenor = tenors_smooth[i + 1]
            if start_tenor < end_tenor:  # Ensure proper ordering
                forward_rate = curve.get_forward_rate(start_tenor, end_tenor)
                forward_rates.append(forward_rate * 100)  # Convert to percentage
                forward_tenors.append(start_tenor)
        
        if forward_rates:  # Only plot if we have valid forward rates
            fig.add_trace(
                go.Scatter(
                    x=forward_tenors,
                    y=forward_rates,
                    mode='lines',
                    name='Forward Rates',
                    line=dict(color='orange', width=2)
                ),
                row=current_row, col=1
            )
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title="Tenor (Years)",
        yaxis_title="Rate (%)",
        height=300 * len(subplot_titles),
        showlegend=True
    )
    
    return fig


def plot_instruments(instruments: List[Instrument], 
                    curve: YieldCurve,
                    market_prices: Optional[List[float]] = None) -> go.Figure:
    """
    Create a plot showing instrument pricing vs market prices.
    
    Args:
        instruments: List of instruments
        curve: Yield curve for pricing
        market_prices: Optional list of market prices
        
    Returns:
        Plotly figure object
    """
    # Calculate model prices
    model_prices = [instrument.price(curve) for instrument in instruments]
    
    # Extract tenors from instruments
    tenors = []
    for instrument in instruments:
        if hasattr(instrument, 'maturity'):
            tenors.append(instrument.maturity)
        else:
            tenors.append((instrument.start_date + instrument.maturity) / 2)
    
    # Create figure
    fig = go.Figure()
    
    # Plot model prices
    fig.add_trace(
        go.Scatter(
            x=tenors,
            y=model_prices,
            mode='markers+lines',
            name='Model Prices',
            marker=dict(size=10, color='blue')
        )
    )
    
    # Plot market prices if provided
    if market_prices is not None:
        fig.add_trace(
            go.Scatter(
                x=tenors,
                y=market_prices,
                mode='markers',
                name='Market Prices',
                marker=dict(size=10, color='red', symbol='x')
            )
        )
        
        # Calculate and display pricing errors
        errors = [(mp - mp_market) / mp_market * 100 if mp_market != 0 else 0 
                 for mp, mp_market in zip(model_prices, market_prices)]
        
        fig.add_trace(
            go.Scatter(
                x=tenors,
                y=errors,
                mode='markers',
                name='Pricing Errors (%)',
                marker=dict(size=8, color='orange'),
                yaxis='y2'
            )
        )
        
        # Add secondary y-axis for errors
        fig.update_layout(
            yaxis2=dict(
                title="Pricing Error (%)",
                overlaying="y",
                side="right"
            )
        )
    
    fig.update_layout(
        title="Instrument Pricing Analysis",
        xaxis_title="Tenor (Years)",
        yaxis_title="Price",
        showlegend=True
    )
    
    return fig


def plot_curve_comparison(curves: List[YieldCurve], 
                         curve_names: List[str],
                         title: str = "Curve Comparison") -> go.Figure:
    """
    Compare multiple yield curves.
    
    Args:
        curves: List of YieldCurve objects
        curve_names: List of curve names
        title: Plot title
        
    Returns:
        Plotly figure object
    """
    fig = go.Figure()
    
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
    
    for i, (curve, name) in enumerate(zip(curves, curve_names)):
        color = colors[i % len(colors)]
        
        # Generate smooth curve for plotting
        tenors_smooth = np.linspace(curve.tenors[0], curve.tenors[-1], 100)
        rates_smooth = [curve.get_rate(t) for t in tenors_smooth]
        
        fig.add_trace(
            go.Scatter(
                x=tenors_smooth,
                y=np.array(rates_smooth) * 100,
                mode='lines',
                name=name,
                line=dict(color=color, width=2)
            )
        )
    
    fig.update_layout(
        title=title,
        xaxis_title="Tenor (Years)",
        yaxis_title="Rate (%)",
        showlegend=True
    )
    
    return fig


def plot_sensitivity_analysis(instrument: Instrument,
                            curve: YieldCurve,
                            shifts: List[float] = None) -> go.Figure:
    """
    Plot sensitivity analysis for an instrument.
    
    Args:
        instrument: Financial instrument
        curve: Yield curve
        shifts: List of rate shifts in basis points
        
    Returns:
        Plotly figure object
    """
    if shifts is None:
        shifts = list(range(-50, 51, 5))  # -50bp to +50bp in 5bp steps
    
    prices = []
    dv01s = []
    
    for shift in shifts:
        shifted_curve = curve.shift_curve(shift)
        price = instrument.price(shifted_curve)
        prices.append(price)
        
        # Calculate DV01
        dv01 = instrument.get_dv01(shifted_curve)
        dv01s.append(dv01)
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=["Price vs Rate Shift", "DV01 vs Rate Shift"],
        vertical_spacing=0.1
    )
    
    # Plot price sensitivity
    fig.add_trace(
        go.Scatter(
            x=shifts,
            y=prices,
            mode='lines+markers',
            name='Price',
            line=dict(color='blue', width=2)
        ),
        row=1, col=1
    )
    
    # Plot DV01
    fig.add_trace(
        go.Scatter(
            x=shifts,
            y=dv01s,
            mode='lines+markers',
            name='DV01',
            line=dict(color='red', width=2)
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title=f"Sensitivity Analysis - {type(instrument).__name__}",
        xaxis_title="Rate Shift (bp)",
        height=600,
        showlegend=True
    )
    
    return fig


def create_dashboard_data(curve: YieldCurve) -> Dict[str, Any]:
    """
    Create data for dashboard display.
    
    Args:
        curve: Yield curve
        
    Returns:
        Dictionary with dashboard data
    """
    # Calculate key metrics
    short_rate = curve.get_rate(0.25) * 100  # 3M rate
    long_rate = curve.get_rate(10.0) * 100   # 10Y rate
    slope = long_rate - short_rate
    
    # Calculate forward rates
    forward_1y = curve.get_forward_rate(0.0, 1.0) * 100
    forward_2y = curve.get_forward_rate(1.0, 2.0) * 100
    
    # Calculate discount factors
    df_1y = curve.get_discount_factor(1.0)
    df_5y = curve.get_discount_factor(5.0)
    df_10y = curve.get_discount_factor(10.0)
    
    return {
        'short_rate': short_rate,
        'long_rate': long_rate,
        'slope': slope,
        'forward_1y': forward_1y,
        'forward_2y': forward_2y,
        'df_1y': df_1y,
        'df_5y': df_5y,
        'df_10y': df_10y,
        'curve_data': curve.to_dataframe()
    } 