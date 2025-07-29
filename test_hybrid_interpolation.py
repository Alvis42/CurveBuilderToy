"""
Demonstration of hybrid interpolation method with cutoff date.
Example: Flat interpolation for short-term SOFR rates, cubic for long-term swap rates.
"""

import numpy as np
import matplotlib.pyplot as plt
from src.core.curve import YieldCurve

def demonstrate_hybrid_interpolation():
    """Demonstrate hybrid interpolation with different cutoff points."""
    
    print("=== Hybrid Interpolation Demonstration ===")
    print("Flat interpolation before cutoff, Cubic interpolation after cutoff")
    
    # Create realistic market data
    # Short-term: FOMC rates (should be flat between meetings)
    # Long-term: Swap rates (should be smooth)
    tenors = [0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 30.0]
    rates = [0.05, 0.0525, 0.055, 0.058, 0.06, 0.062, 0.064, 0.065, 0.0655]
    
    cutoff_tenor = 2.0  # 2-year cutoff between SOFR and swaps
    
    # Create different curves for comparison
    curves = {
        'Hybrid (Flat->Cubic)': YieldCurve(tenors, rates, 
                                         interpolation_method='hybrid',
                                         cutoff_tenor=cutoff_tenor,
                                         pre_cutoff_method='flat',
                                         post_cutoff_method='cubic'),
        'Pure Cubic': YieldCurve(tenors, rates, interpolation_method='cubic'),
        'Pure Flat': YieldCurve(tenors, rates, interpolation_method='flat'),
        'Pure Linear': YieldCurve(tenors, rates, interpolation_method='linear')
    }
    
    # Test specific points
    test_tenors = [0.1, 0.3, 0.75, 1.5, 2.5, 4.0, 7.0, 15.0, 25.0]
    
    print(f"\n{'Tenor':<8} {'Hybrid':<12} {'Cubic':<12} {'Flat':<12} {'Linear':<12}")
    print("-" * 60)
    
    for tenor in test_tenors:
        hybrid_rate = curves['Hybrid (Flat->Cubic)'].get_rate(tenor)
        cubic_rate = curves['Pure Cubic'].get_rate(tenor)
        flat_rate = curves['Pure Flat'].get_rate(tenor)
        linear_rate = curves['Pure Linear'].get_rate(tenor)
        
        print(f"{tenor:<8.2f} {hybrid_rate:<12.6f} {cubic_rate:<12.6f} {flat_rate:<12.6f} {linear_rate:<12.6f}")
    
    # Create detailed visualization
    tenors_smooth = np.linspace(0.1, 30.0, 1000)
    
    plt.figure(figsize=(15, 10))
    
    # Main plot
    plt.subplot(2, 2, 1)
    for name, curve in curves.items():
        rates_smooth = [curve.get_rate(t) for t in tenors_smooth]
        plt.plot(tenors_smooth, np.array(rates_smooth) * 100, 
                label=name, linewidth=2)
    
    # Plot original points
    plt.plot(tenors, np.array(rates) * 100, 'ko', markersize=6, label='Market Data')
    
    # Add cutoff line
    plt.axvline(x=cutoff_tenor, color='red', linestyle='--', alpha=0.7, 
                label=f'Cutoff at {cutoff_tenor}Y')
    
    plt.xlabel('Tenor (years)')
    plt.ylabel('Rate (%)')
    plt.title('Hybrid Interpolation: Flat (≤2Y) + Cubic (>2Y)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Zoom on short end
    plt.subplot(2, 2, 2)
    short_tenors = tenors_smooth[tenors_smooth <= 5.0]
    for name, curve in curves.items():
        short_rates = [curve.get_rate(t) for t in short_tenors]
        plt.plot(short_tenors, np.array(short_rates) * 100, 
                label=name, linewidth=2)
    
    plt.plot([t for t in tenors if t <= 5.0], 
             [r * 100 for t, r in zip(tenors, rates) if t <= 5.0], 
             'ko', markersize=6)
    plt.axvline(x=cutoff_tenor, color='red', linestyle='--', alpha=0.7)
    plt.xlabel('Tenor (years)')
    plt.ylabel('Rate (%)')
    plt.title('Short End Detail (≤5Y)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Zoom on long end
    plt.subplot(2, 2, 3)
    long_tenors = tenors_smooth[tenors_smooth >= 2.0]
    for name, curve in curves.items():
        long_rates = [curve.get_rate(t) for t in long_tenors]
        plt.plot(long_tenors, np.array(long_rates) * 100, 
                label=name, linewidth=2)
    
    plt.plot([t for t in tenors if t >= 2.0], 
             [r * 100 for t, r in zip(tenors, rates) if t >= 2.0], 
             'ko', markersize=6)
    plt.axvline(x=cutoff_tenor, color='red', linestyle='--', alpha=0.7)
    plt.xlabel('Tenor (years)')
    plt.ylabel('Rate (%)')
    plt.title('Long End Detail (≥2Y)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Show rate differences
    plt.subplot(2, 2, 4)
    hybrid_rates = [curves['Hybrid (Flat->Cubic)'].get_rate(t) for t in tenors_smooth]
    cubic_rates = [curves['Pure Cubic'].get_rate(t) for t in tenors_smooth]
    
    diff_bp = (np.array(hybrid_rates) - np.array(cubic_rates)) * 10000
    plt.plot(tenors_smooth, diff_bp, linewidth=2, color='red')
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    plt.axvline(x=cutoff_tenor, color='red', linestyle='--', alpha=0.7)
    plt.xlabel('Tenor (years)')
    plt.ylabel('Rate Difference (bp)')
    plt.title('Hybrid vs Pure Cubic (basis points)')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('hybrid_interpolation_demo.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"\n=== Hybrid Interpolation Analysis ===")
    print(f"Cutoff Tenor: {cutoff_tenor} years")
    print(f"Pre-cutoff Method: Flat (SOFR-style)")
    print(f"Post-cutoff Method: Cubic (Swap-style)")
    print(f"\n✅ Benefits:")
    print(f"• Realistic short-term rate behavior (flat between FOMC meetings)")
    print(f"• Smooth long-term curve (important for swap pricing)")
    print(f"• Seamless transition at cutoff point")
    print(f"• Reflects real market structure")

def test_different_cutoff_points():
    """Test hybrid interpolation with different cutoff points."""
    
    print("\n=== Testing Different Cutoff Points ===")
    
    tenors = [0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
    rates = [0.05, 0.0525, 0.055, 0.06, 0.062, 0.065]
    
    cutoff_points = [0.5, 1.0, 2.0, 5.0]
    
    plt.figure(figsize=(12, 8))
    tenors_smooth = np.linspace(0.1, 10.0, 200)
    
    for i, cutoff in enumerate(cutoff_points):
        curve = YieldCurve(tenors, rates,
                          interpolation_method='hybrid',
                          cutoff_tenor=cutoff,
                          pre_cutoff_method='flat',
                          post_cutoff_method='cubic')
        
        rates_smooth = [curve.get_rate(t) for t in tenors_smooth]
        plt.plot(tenors_smooth, np.array(rates_smooth) * 100, 
                label=f'Cutoff at {cutoff}Y', linewidth=2)
        plt.axvline(x=cutoff, color=f'C{i}', linestyle='--', alpha=0.5)
    
    # Plot original points
    plt.plot(tenors, np.array(rates) * 100, 'ko', markersize=8, label='Market Data')
    
    plt.xlabel('Tenor (years)')
    plt.ylabel('Rate (%)')
    plt.title('Hybrid Interpolation with Different Cutoff Points')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('hybrid_cutoff_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

def test_different_method_combinations():
    """Test different combinations of pre/post cutoff methods."""
    
    print("\n=== Testing Different Method Combinations ===")
    
    tenors = [0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
    rates = [0.05, 0.0525, 0.055, 0.06, 0.062, 0.065]
    cutoff = 2.0
    
    combinations = [
        ('flat', 'cubic', 'Flat -> Cubic'),
        ('flat', 'linear', 'Flat -> Linear'),
        ('linear', 'cubic', 'Linear -> Cubic'),
        ('flat', 'log_linear', 'Flat -> Log-Linear'),
    ]
    
    plt.figure(figsize=(12, 8))
    tenors_smooth = np.linspace(0.1, 10.0, 200)
    
    for pre_method, post_method, label in combinations:
        try:
            curve = YieldCurve(tenors, rates,
                              interpolation_method='hybrid',
                              cutoff_tenor=cutoff,
                              pre_cutoff_method=pre_method,
                              post_cutoff_method=post_method)
            
            rates_smooth = [curve.get_rate(t) for t in tenors_smooth]
            plt.plot(tenors_smooth, np.array(rates_smooth) * 100, 
                    label=label, linewidth=2)
        except Exception as e:
            print(f"Error with {label}: {e}")
    
    # Plot original points and cutoff
    plt.plot(tenors, np.array(rates) * 100, 'ko', markersize=8, label='Market Data')
    plt.axvline(x=cutoff, color='red', linestyle='--', alpha=0.7, label=f'Cutoff at {cutoff}Y')
    
    plt.xlabel('Tenor (years)')
    plt.ylabel('Rate (%)')
    plt.title('Different Hybrid Method Combinations')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('hybrid_method_combinations.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    demonstrate_hybrid_interpolation()
    test_different_cutoff_points()
    test_different_method_combinations() 