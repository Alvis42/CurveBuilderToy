"""
Test and demonstration of the new flat interpolation method.
Suitable for SOFR/Fed Fund rates based on FOMC announcements.
"""

import numpy as np
import matplotlib.pyplot as plt
from src.core.curve import YieldCurve

def test_flat_interpolation():
    """Test the flat interpolation method with FOMC-style rate data."""
    
    print("=== Testing Flat Interpolation Method ===")
    print("Simulating SOFR/Fed Fund rates with FOMC announcement dates")
    
    # Simulate FOMC meeting dates and rate decisions
    fomc_dates = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 5.0]  # Quarters
    fed_rates = [0.05, 0.05, 0.0525, 0.055, 0.055, 0.06, 0.065, 0.07, 0.07]  # Rate decisions
    
    # Create curves with different interpolation methods
    curve_flat = YieldCurve(fomc_dates, fed_rates, interpolation_method='flat')
    curve_linear = YieldCurve(fomc_dates, fed_rates, interpolation_method='linear')
    curve_cubic = YieldCurve(fomc_dates, fed_rates, interpolation_method='cubic')
    
    # Test specific points
    test_tenors = [0.1, 0.3, 0.6, 0.8, 1.1, 1.7, 2.5, 4.0, 6.0]
    
    print(f"\n{'Tenor':<8} {'Flat Rate':<12} {'Linear Rate':<12} {'Cubic Rate':<12}")
    print("-" * 50)
    
    for tenor in test_tenors:
        flat_rate = curve_flat.get_rate(tenor)
        linear_rate = curve_linear.get_rate(tenor)
        cubic_rate = curve_cubic.get_rate(tenor)
        
        print(f"{tenor:<8.2f} {flat_rate:<12.6f} {linear_rate:<12.6f} {cubic_rate:<12.6f}")
    
    # Create visualization
    tenors_smooth = np.linspace(0.1, 6.0, 200)
    
    rates_flat = [curve_flat.get_rate(t) for t in tenors_smooth]
    rates_linear = [curve_linear.get_rate(t) for t in tenors_smooth]
    rates_cubic = [curve_cubic.get_rate(t) for t in tenors_smooth]
    
    plt.figure(figsize=(12, 8))
    
    # Plot interpolated curves
    plt.plot(tenors_smooth, np.array(rates_flat) * 100, 
             label='Flat (FOMC-style)', linewidth=2, linestyle='-', color='red')
    plt.plot(tenors_smooth, np.array(rates_linear) * 100, 
             label='Linear', linewidth=2, linestyle='--', color='blue')
    plt.plot(tenors_smooth, np.array(rates_cubic) * 100, 
             label='Cubic', linewidth=2, linestyle='-.', color='green')
    
    # Plot original points
    plt.plot(fomc_dates, np.array(fed_rates) * 100, 
             'o', markersize=8, color='black', label='FOMC Decisions')
    
    # Add vertical lines for FOMC meetings
    for date in fomc_dates:
        plt.axvline(x=date, color='gray', linestyle=':', alpha=0.5)
    
    plt.xlabel('Tenor (years)')
    plt.ylabel('Rate (%)')
    plt.title('Interpolation Methods Comparison: SOFR/Fed Fund Rates')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 6)
    
    # Add annotations
    plt.text(0.5, 6.8, 'FOMC Meeting Dates', fontsize=10, alpha=0.7)
    plt.text(3.5, 5.2, 'Flat interpolation maintains\nconstant rates between\nFOMC meetings', 
             fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
    
    plt.tight_layout()
    plt.savefig('flat_interpolation_demo.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("\n=== Characteristics of Flat Interpolation ===")
    print("✅ Rates stay constant between FOMC meetings")
    print("✅ Reflects reality of Fed Fund rate setting")
    print("✅ No artificial smoothing between rate decisions")
    print("✅ Perfect for short-term funding curves")
    print("✅ Maintains regulatory/central bank policy intent")
    
    print("\n=== Use Cases ===")
    print("• SOFR curve construction")
    print("• Fed Fund rate curves")
    print("• Central bank policy rate modeling")
    print("• Short-term funding cost analysis")
    print("• Overnight index swap (OIS) curves")

def test_flat_interpolation_edge_cases():
    """Test edge cases for flat interpolation."""
    
    print("\n=== Testing Edge Cases ===")
    
    # Test with different curve shapes
    tenors = [0.25, 1.0, 2.0, 5.0]
    
    test_cases = [
        ([0.05, 0.05, 0.05, 0.05], "Flat curve"),
        ([0.02, 0.04, 0.06, 0.08], "Rising curve"),
        ([0.08, 0.06, 0.04, 0.02], "Falling curve"),
        ([0.03, 0.05, 0.04, 0.06], "Humped curve")
    ]
    
    for rates, description in test_cases:
        print(f"\n{description}:")
        curve = YieldCurve(tenors, rates, interpolation_method='flat')
        
        test_points = [0.1, 0.5, 1.5, 3.0, 6.0]
        for tenor in test_points:
            rate = curve.get_rate(tenor)
            print(f"  Tenor {tenor:4.1f}y: {rate:6.4f} ({rate*100:5.2f}%)")

if __name__ == "__main__":
    test_flat_interpolation()
    test_flat_interpolation_edge_cases() 