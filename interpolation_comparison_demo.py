"""
Demo script to compare linear vs log-linear interpolation methods.
"""

import numpy as np
import matplotlib.pyplot as plt
from src.core.curve import YieldCurve

def demonstrate_interpolation_differences():
    """Demonstrate the differences between linear and log-linear interpolation."""
    
    # Sample data points
    tenors = [0.5, 1.0, 2.0, 5.0, 10.0]
    rates = [0.02, 0.025, 0.03, 0.035, 0.04]
    
    # Create curves with different interpolation methods
    curve_linear = YieldCurve(tenors, rates, interpolation_method='linear')
    curve_log_linear = YieldCurve(tenors, rates, interpolation_method='log_linear')
    
    # Generate smooth tenors for plotting
    tenors_smooth = np.linspace(0.1, 10.0, 100)
    
    # Calculate rates for both methods
    rates_linear = [curve_linear.get_rate(t) for t in tenors_smooth]
    rates_log_linear = [curve_log_linear.get_rate(t) for t in tenors_smooth]
    
    # Calculate discount factors for both methods
    df_linear = [curve_linear.get_discount_factor(t) for t in tenors_smooth]
    df_log_linear = [curve_log_linear.get_discount_factor(t) for t in tenors_smooth]
    
    # Create plots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Plot 1: Rates comparison
    ax1.plot(tenors, rates, 'o', label='Original points', markersize=8)
    ax1.plot(tenors_smooth, rates_linear, label='Linear interpolation', linewidth=2)
    ax1.plot(tenors_smooth, rates_log_linear, label='Log-linear interpolation', linewidth=2)
    ax1.set_xlabel('Tenor (years)')
    ax1.set_ylabel('Rate')
    ax1.set_title('Rate Interpolation Comparison')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Discount factors comparison
    original_df = [np.exp(-t * r) for t, r in zip(tenors, rates)]
    ax2.plot(tenors, original_df, 'o', label='Original points', markersize=8)
    ax2.plot(tenors_smooth, df_linear, label='Linear interpolation', linewidth=2)
    ax2.plot(tenors_smooth, df_log_linear, label='Log-linear interpolation', linewidth=2)
    ax2.set_xlabel('Tenor (years)')
    ax2.set_ylabel('Discount Factor')
    ax2.set_title('Discount Factor Interpolation Comparison')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Rate differences
    rate_diff = np.array(rates_log_linear) - np.array(rates_linear)
    ax3.plot(tenors_smooth, rate_diff * 10000, linewidth=2, color='red')
    ax3.set_xlabel('Tenor (years)')
    ax3.set_ylabel('Rate Difference (basis points)')
    ax3.set_title('Rate Difference: Log-linear - Linear')
    ax3.grid(True, alpha=0.3)
    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # Plot 4: Discount factor differences
    df_diff = np.array(df_log_linear) - np.array(df_linear)
    ax4.plot(tenors_smooth, df_diff * 100, linewidth=2, color='red')
    ax4.set_xlabel('Tenor (years)')
    ax4.set_ylabel('Discount Factor Difference (%)')
    ax4.set_title('Discount Factor Difference: Log-linear - Linear')
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig('interpolation_methods_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print numerical examples
    print("\n=== Numerical Examples ===")
    print(f"{'Tenor':<8} {'Linear Rate':<12} {'Log-Linear Rate':<15} {'Diff (bp)':<10}")
    print("-" * 50)
    
    for tenor in [0.25, 0.75, 1.5, 3.0, 7.0]:
        linear_rate = curve_linear.get_rate(tenor)
        log_linear_rate = curve_log_linear.get_rate(tenor)
        diff_bp = (log_linear_rate - linear_rate) * 10000
        print(f"{tenor:<8.2f} {linear_rate:<12.6f} {log_linear_rate:<15.6f} {diff_bp:<10.2f}")
    
    print("\n=== Key Differences ===")
    print("1. Linear interpolation: Direct rate interpolation")
    print("2. Log-linear interpolation: Interpolates log discount factors")
    print("3. Log-linear guarantees positive rates and discount factors")
    print("4. Log-linear better preserves no-arbitrage conditions")
    print("5. Differences are typically small but important for pricing")

if __name__ == "__main__":
    demonstrate_interpolation_differences() 