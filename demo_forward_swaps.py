"""
Demonstration of Forward Starting Swap Pricing and Curve Construction
=====================================================================

This script demonstrates:
1. Forward starting swap pricing
2. Par rate calculation for forward swaps
3. Curve construction with mixed spot and forward swaps
4. Analysis of forward swap coverage
5. Sensitivity analysis for forward rate segments
"""

import numpy as np
import matplotlib.pyplot as plt
from src.core.curve import YieldCurve
from src.core.instruments import IRSwap
from src.core.bootstrapping import CurveBootstrapper


def demonstrate_forward_swap_pricing():
    """Demonstrate forward starting swap pricing."""
    
    print("=" * 60)
    print("FORWARD STARTING SWAP PRICING DEMONSTRATION")
    print("=" * 60)
    
    # Create a base curve for pricing
    tenors = [0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0]
    rates = [0.02, 0.025, 0.03, 0.035, 0.04, 0.042, 0.045]
    curve = YieldCurve(tenors, rates, interpolation_method='cubic')
    
    print("\n📊 Base Yield Curve:")
    for tenor, rate in zip(tenors, rates):
        print(f"  {tenor:>4.1f}Y: {rate:>6.3%}")
    
    # Create different types of swaps
    swaps = [
        IRSwap(0.0, 5.0, 0.04),      # Spot 5Y swap
        IRSwap(1.0, 5.0, 0.04),      # 1Y forward 4Y swap (1Y-5Y)
        IRSwap(2.0, 7.0, 0.04),      # 2Y forward 5Y swap (2Y-7Y)
        IRSwap(3.0, 10.0, 0.04),     # 3Y forward 7Y swap (3Y-10Y)
    ]
    
    print("\n💰 Swap Pricing Results:")
    print(f"{'Swap Type':<20} {'Price':<12} {'Par Rate':<10} {'DV01':<10}")
    print("-" * 55)
    
    for swap in swaps:
        price = swap.price(curve)
        par_rate = swap.get_par_rate(curve)
        dv01 = swap.get_dv01(curve)
        
        swap_type = f"{swap.start_date}Y-{swap.maturity}Y"
        if swap.is_forward_starting:
            swap_type += " (Fwd)"
        else:
            swap_type += " (Spot)"
            
        print(f"{swap_type:<20} {price:>10.6f} {par_rate:>9.3%} {dv01:>9.2f}")
    
    return swaps, curve


def demonstrate_curve_construction():
    """Demonstrate curve construction with forward starting swaps."""
    
    print("\n" + "=" * 60)
    print("CURVE CONSTRUCTION WITH FORWARD STARTING SWAPS")
    print("=" * 60)
    
    # Create a mix of spot and forward starting swaps for curve building
    instruments = [
        IRSwap(0.0, 1.0, 0.025),     # 1Y spot swap
        IRSwap(0.0, 2.0, 0.030),     # 2Y spot swap  
        IRSwap(2.0, 5.0, 0.040),     # 2Y-5Y forward swap (controls 2Y-5Y segment)
        IRSwap(5.0, 10.0, 0.045),    # 5Y-10Y forward swap (controls 5Y-10Y segment)
    ]
    
    # For par swaps, market prices should be 0.0
    market_prices = [0.0, 0.0, 0.0, 0.0]
    
    print("\n🔧 Input Instruments:")
    for i, instrument in enumerate(instruments):
        print(f"  {i+1}. {instrument} - Market Price: {market_prices[i]}")
    
    # Bootstrap the curve
    bootstrapper = CurveBootstrapper(interpolation_method='cubic')
    
    # Analyze coverage first
    coverage = bootstrapper.analyze_forward_swap_coverage(instruments)
    print(f"\n📋 Forward Swap Coverage Analysis:")
    print(f"  Total instruments: {coverage['total_instruments']}")
    print(f"  Forward starting: {coverage['forward_starting_count']}")
    print(f"  Spot starting: {coverage['spot_starting_count']}")
    print(f"  Curve range: {coverage['min_tenor']:.1f}Y - {coverage['max_tenor']:.1f}Y")
    
    print(f"\n📊 Coverage Segments:")
    for segment in coverage['coverage_segments']:
        print(f"  {segment['instrument']} covers {segment['start_tenor']:.1f}Y-{segment['end_tenor']:.1f}Y ({segment['type']})")
    
    # Bootstrap curve
    try:
        curve = bootstrapper.bootstrap_with_forward_control(instruments, market_prices)
        
        print(f"\n✅ Curve Construction Successful!")
        print(f"   Curve tenors: {[f'{t:.1f}Y' for t in curve.tenors]}")
        print(f"   Curve rates: {[f'{r:.3%}' for r in curve.rates]}")
        
        # Verify instruments price to zero (par condition)
        print(f"\n🔍 Verification (should be close to 0.0 for par swaps):")
        for i, instrument in enumerate(instruments):
            price = instrument.price(curve)
            par_rate = instrument.get_par_rate(curve)
            print(f"  {instrument}: Price = {price:>8.6f}, Par Rate = {par_rate:>6.3%}")
            
    except Exception as e:
        print(f"\n❌ Curve construction failed: {e}")
        return None
    
    return curve, instruments


def demonstrate_forward_rate_sensitivity():
    """Demonstrate forward rate sensitivity analysis."""
    
    print("\n" + "=" * 60)
    print("FORWARD RATE SENSITIVITY ANALYSIS")
    print("=" * 60)
    
    # Create curve and swaps
    tenors = [1.0, 2.0, 3.0, 5.0, 7.0, 10.0]
    rates = [0.025, 0.03, 0.035, 0.04, 0.042, 0.045]
    curve = YieldCurve(tenors, rates, interpolation_method='cubic')
    
    # Create forward starting swaps
    forward_swaps = [
        IRSwap(1.0, 3.0, 0.035),    # 1Y-3Y forward swap
        IRSwap(2.0, 5.0, 0.040),    # 2Y-5Y forward swap
        IRSwap(5.0, 10.0, 0.043),   # 5Y-10Y forward swap
    ]
    
    print("\n📈 Forward Rate Sensitivity Analysis:")
    print("Testing sensitivity to 1bp shocks in different forward rate segments")
    
    # Define forward rate segments to test
    rate_segments = [
        (1.0, 2.0), (2.0, 3.0), (3.0, 5.0), (5.0, 7.0), (7.0, 10.0)
    ]
    
    print(f"\n{'Swap':<15} {'Segment':<10} {'Sensitivity':<12} {'Explanation'}")
    print("-" * 70)
    
    for swap in forward_swaps:
        print(f"\n{str(swap):<15}")
        
        for start_seg, end_seg in rate_segments:
            # Calculate analytical sensitivity
            sensitivity = swap.get_forward_rate_sensitivity(curve, start_seg, end_seg)
            
            # Determine if this segment affects the swap
            swap_start, swap_end = swap.forward_tenor_range
            
            if start_seg >= swap_start and end_seg <= swap_end:
                explanation = "✓ Directly affects swap"
            elif end_seg <= swap_start or start_seg >= swap_end:
                explanation = "✗ Outside swap period"
            else:
                explanation = "~ Partial overlap"
            
            print(f"{'':15} {start_seg}-{end_seg}Y     {sensitivity:>10.4f}  {explanation}")


def demonstrate_par_rate_calculation():
    """Demonstrate par rate calculation for different swap structures."""
    
    print("\n" + "=" * 60)
    print("PAR RATE CALCULATION FOR FORWARD STARTING SWAPS")
    print("=" * 60)
    
    # Create different curve scenarios
    scenarios = {
        'Flat 4%': ([1, 2, 3, 5, 7, 10], [0.04, 0.04, 0.04, 0.04, 0.04, 0.04]),
        'Upward Sloping': ([1, 2, 3, 5, 7, 10], [0.02, 0.025, 0.03, 0.035, 0.04, 0.045]),
        'Inverted': ([1, 2, 3, 5, 7, 10], [0.05, 0.045, 0.04, 0.035, 0.03, 0.025]),
    }
    
    # Define swap structures
    swap_structures = [
        ('1Y Spot', IRSwap(0.0, 1.0, 0.03)),
        ('2Y Spot', IRSwap(0.0, 2.0, 0.03)),
        ('1Y-3Y Fwd', IRSwap(1.0, 3.0, 0.03)),
        ('2Y-5Y Fwd', IRSwap(2.0, 5.0, 0.03)),
        ('5Y-10Y Fwd', IRSwap(5.0, 10.0, 0.03)),
    ]
    
    print(f"\n{'Scenario':<15} {'1Y Spot':<10} {'2Y Spot':<10} {'1Y-3Y Fwd':<12} {'2Y-5Y Fwd':<12} {'5Y-10Y Fwd':<12}")
    print("-" * 85)
    
    for scenario_name, (tenors, rates) in scenarios.items():
        curve = YieldCurve(tenors, rates, interpolation_method='cubic')
        
        par_rates = []
        for _, swap in swap_structures:
            try:
                par_rate = swap.get_par_rate(curve)
                par_rates.append(f"{par_rate:>8.3%}")
            except:
                par_rates.append("   N/A")
        
        print(f"{scenario_name:<15} {par_rates[0]:<10} {par_rates[1]:<10} {par_rates[2]:<12} {par_rates[3]:<12} {par_rates[4]:<12}")


def visualize_forward_swap_coverage():
    """Create a visualization of forward swap coverage."""
    
    print("\n" + "=" * 60)
    print("FORWARD SWAP COVERAGE VISUALIZATION")
    print("=" * 60)
    
    # Create instruments
    instruments = [
        IRSwap(0.0, 2.0, 0.025),     # 2Y spot
        IRSwap(0.0, 5.0, 0.035),     # 5Y spot  
        IRSwap(2.0, 5.0, 0.040),     # 2Y-5Y forward
        IRSwap(5.0, 10.0, 0.045),    # 5Y-10Y forward
        IRSwap(1.0, 3.0, 0.030),     # 1Y-3Y forward
    ]
    
    plt.figure(figsize=(12, 8))
    
    colors = ['blue', 'green', 'red', 'orange', 'purple']
    y_positions = range(len(instruments))
    
    for i, instrument in enumerate(instruments):
        start = instrument.start_date
        end = instrument.maturity
        
        # Draw the coverage bar
        plt.barh(i, end - start, left=start, height=0.6, 
                color=colors[i % len(colors)], alpha=0.7,
                label=f"{instrument}")
        
        # Add text annotation
        mid_point = (start + end) / 2
        plt.text(mid_point, i, f"{start}Y-{end}Y", 
                ha='center', va='center', fontweight='bold', fontsize=9)
    
    plt.xlabel('Tenor (Years)')
    plt.ylabel('Instruments')
    plt.title('Forward Starting Swap Coverage Analysis\nShowing which parts of the curve each swap controls')
    plt.grid(True, alpha=0.3, axis='x')
    
    # Customize y-axis
    plt.yticks(y_positions, [f"Swap {i+1}" for i in y_positions])
    
    # Add legend
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.savefig('forward_swap_coverage.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("📊 Coverage visualization saved as 'forward_swap_coverage.png'")


def main():
    """Run all forward starting swap demonstrations."""
    
    print("🚀 FORWARD STARTING SWAP DEMONSTRATION")
    print("=====================================")
    print("This demo shows forward starting swap pricing and curve construction")
    print("Forward swaps control specific curve segments, perfect for targeted curve building")
    
    try:
        # Run demonstrations
        demonstrate_forward_swap_pricing()
        demonstrate_curve_construction()
        demonstrate_forward_rate_sensitivity()
        demonstrate_par_rate_calculation()
        visualize_forward_swap_coverage()
        
        print("\n" + "=" * 60)
        print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\n✨ Key Takeaways:")
        print("• Forward starting swaps control specific curve segments")
        print("• They're essential for building realistic yield curves")
        print("• Par rates vary significantly based on curve shape")
        print("• Forward rate sensitivity helps understand risk exposure")
        print("• Mixed spot/forward instruments provide complete curve control")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 