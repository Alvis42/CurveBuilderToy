#!/usr/bin/env python3
"""
Demonstration of different interpolation methods for yield curves.
"""

import numpy as np
import matplotlib.pyplot as plt
from src.core.curve import YieldCurve

def demonstrate_interpolation():
    """Show the differences between interpolation methods."""
    
    # Sample market data
    tenors = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
    rates = [0.025, 0.0275, 0.03, 0.0325, 0.035, 0.0375]  # 2.5% to 3.75%
    
    # Create curves with different interpolation methods
    linear_curve = YieldCurve(tenors, rates, 'linear')
    cubic_curve = YieldCurve(tenors, rates, 'cubic')
    log_linear_curve = YieldCurve(tenors, rates, 'log_linear')
    
    # Generate smooth curve for plotting
    tenors_smooth = np.linspace(0.5, 10.0, 100)
    
    # Get rates for each method
    linear_rates = [linear_curve.get_rate(t) for t in tenors_smooth]
    cubic_rates = [cubic_curve.get_rate(t) for t in tenors_smooth]
    log_linear_rates = [log_linear_curve.get_rate(t) for t in tenors_smooth]
    
    # Plot comparison
    plt.figure(figsize=(12, 8))
    
    # Plot rates
    plt.subplot(2, 2, 1)
    plt.plot(tenors, [r*100 for r in rates], 'ro', markersize=8, label='Market Points')
    plt.plot(tenors_smooth, [r*100 for r in linear_rates], 'b-', label='Linear', linewidth=2)
    plt.plot(tenors_smooth, [r*100 for r in cubic_rates], 'g-', label='Cubic', linewidth=2)
    plt.plot(tenors_smooth, [r*100 for r in log_linear_rates], 'orange', label='Log-Linear', linewidth=2)
    plt.xlabel('Tenor (Years)')
    plt.ylabel('Rate (%)')
    plt.title('Zero-Coupon Rates')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot discount factors
    plt.subplot(2, 2, 2)
    linear_dfs = [linear_curve.get_discount_factor(t) for t in tenors_smooth]
    cubic_dfs = [cubic_curve.get_discount_factor(t) for t in tenors_smooth]
    log_linear_dfs = [log_linear_curve.get_discount_factor(t) for t in tenors_smooth]
    
    plt.plot(tenors_smooth, linear_dfs, 'b-', label='Linear', linewidth=2)
    plt.plot(tenors_smooth, cubic_dfs, 'g-', label='Cubic', linewidth=2)
    plt.plot(tenors_smooth, log_linear_dfs, 'orange', label='Log-Linear', linewidth=2)
    plt.xlabel('Tenor (Years)')
    plt.ylabel('Discount Factor')
    plt.title('Discount Factors')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot forward rates
    plt.subplot(2, 2, 3)
    forward_tenors = tenors_smooth[:-1]
    linear_forwards = [linear_curve.get_forward_rate(tenors_smooth[i], tenors_smooth[i+1]) 
                      for i in range(len(tenors_smooth)-1)]
    cubic_forwards = [cubic_curve.get_forward_rate(tenors_smooth[i], tenors_smooth[i+1]) 
                     for i in range(len(tenors_smooth)-1)]
    log_linear_forwards = [log_linear_curve.get_forward_rate(tenors_smooth[i], tenors_smooth[i+1]) 
                          for i in range(len(tenors_smooth)-1)]
    
    plt.plot(forward_tenors, [f*100 for f in linear_forwards], 'b-', label='Linear', linewidth=2)
    plt.plot(forward_tenors, [f*100 for f in cubic_forwards], 'g-', label='Cubic', linewidth=2)
    plt.plot(forward_tenors, [f*100 for f in log_linear_forwards], 'orange', label='Log-Linear', linewidth=2)
    plt.xlabel('Tenor (Years)')
    plt.ylabel('Forward Rate (%)')
    plt.title('Forward Rates')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot differences from linear
    plt.subplot(2, 2, 4)
    cubic_diff = [(c - l)*100 for c, l in zip(cubic_rates, linear_rates)]
    log_linear_diff = [(ll - l)*100 for ll, l in zip(log_linear_rates, linear_rates)]
    
    plt.plot(tenors_smooth, cubic_diff, 'g-', label='Cubic - Linear', linewidth=2)
    plt.plot(tenors_smooth, log_linear_diff, 'orange', label='Log-Linear - Linear', linewidth=2)
    plt.xlabel('Tenor (Years)')
    plt.ylabel('Rate Difference (bp)')
    plt.title('Difference from Linear Interpolation')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('interpolation_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Print some key metrics
    print("Interpolation Method Comparison:")
    print("=" * 50)
    
    # Test at some intermediate points
    test_tenors = [1.5, 4.0, 7.5]
    print(f"{'Tenor':<8} {'Linear':<10} {'Cubic':<10} {'Log-Linear':<12}")
    print("-" * 40)
    
    for tenor in test_tenors:
        linear_rate = linear_curve.get_rate(tenor) * 100
        cubic_rate = cubic_curve.get_rate(tenor) * 100
        log_linear_rate = log_linear_curve.get_rate(tenor) * 100
        print(f"{tenor:<8.1f} {linear_rate:<10.3f} {cubic_rate:<10.3f} {log_linear_rate:<12.3f}")
    
    print("\nKey Observations:")
    print("- Linear: Straight lines between points")
    print("- Cubic: Smooth curves, may overshoot")
    print("- Log-Linear: Interpolates discount factors, more stable")

if __name__ == "__main__":
    demonstrate_interpolation() 