"""
Analysis of Overlapping Forward Starting Swaps
==============================================

This script analyzes what happens when forward starting swaps overlap:
1. How overlapping swaps affect curve construction
2. Sensitivity analysis for overlapping periods
3. Over-determination and under-determination scenarios
4. Best practices for handling overlapping instruments
"""

import numpy as np
import matplotlib.pyplot as plt
from src.core.curve import YieldCurve
from src.core.instruments import IRSwap
from src.core.bootstrapping import CurveBootstrapper


def analyze_overlapping_swaps():
    """Analyze behavior with overlapping forward starting swaps."""
    
    print("=" * 70)
    print("OVERLAPPING FORWARD STARTING SWAPS ANALYSIS")
    print("=" * 70)
    
    print("\n📊 Scenario: Multiple swaps controlling overlapping curve segments")
    
    # Create overlapping forward starting swaps
    instruments = [
        IRSwap(0.0, 2.0, 0.030),     # 0-2Y (spot)
        IRSwap(1.0, 4.0, 0.035),     # 1-4Y (overlaps with spot and next forward)
        IRSwap(2.0, 5.0, 0.040),     # 2-5Y (overlaps with previous)
        IRSwap(3.0, 7.0, 0.042),     # 3-7Y (overlaps with previous)
        IRSwap(5.0, 10.0, 0.045),    # 5-10Y (overlaps at 5Y boundary)
    ]
    
    # Par swaps (zero market prices)
    market_prices = [0.0, 0.0, 0.0, 0.0, 0.0]
    
    print("\n🔧 Overlapping Instruments:")
    for i, instrument in enumerate(instruments):
        print(f"  {i+1}. {instrument} - Market Price: {market_prices[i]}")
    
    # Analyze coverage
    bootstrapper = CurveBootstrapper(interpolation_method='cubic')
    coverage = bootstrapper.analyze_forward_swap_coverage(instruments)
    
    print(f"\n📋 Coverage Analysis:")
    print(f"  Total instruments: {coverage['total_instruments']}")
    print(f"  Forward starting: {coverage['forward_starting_count']}")
    print(f"  Spot starting: {coverage['spot_starting_count']}")
    print(f"  Curve range: {coverage['min_tenor']:.1f}Y - {coverage['max_tenor']:.1f}Y")
    
    print(f"\n📊 Detailed Coverage (showing overlaps):")
    for segment in coverage['coverage_segments']:
        print(f"  {segment['instrument']} covers {segment['start_tenor']:.1f}Y-{segment['end_tenor']:.1f}Y ({segment['type']})")
    
    # Identify overlapping regions
    print(f"\n⚠️  Overlapping Regions:")
    overlaps = find_overlapping_regions(instruments)
    for overlap in overlaps:
        print(f"  {overlap['start']:.1f}Y-{overlap['end']:.1f}Y: {len(overlap['instruments'])} instruments")
        for inst in overlap['instruments']:
            print(f"    - {inst}")
    
    return instruments, overlaps


def find_overlapping_regions(instruments):
    """Find regions where multiple instruments overlap."""
    # Create a list of all tenor breakpoints
    breakpoints = set()
    for inst in instruments:
        if hasattr(inst, 'is_forward_starting'):
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
            if hasattr(inst, 'is_forward_starting'):
                if inst.start_date <= mid_point <= inst.maturity:
                    covering_instruments.append(str(inst))
        
        if len(covering_instruments) > 1:
            overlaps.append({
                'start': start,
                'end': end,
                'instruments': covering_instruments
            })
    
    return overlaps


def demonstrate_overdetermination():
    """Demonstrate what happens with over-determined systems."""
    
    print("\n" + "=" * 70)
    print("OVER-DETERMINATION ANALYSIS")
    print("=" * 70)
    
    print("\n🎯 Creating system with more instruments than curve points")
    
    # Create many overlapping instruments for limited curve space
    instruments = [
        IRSwap(0.0, 2.0, 0.030),     # 0-2Y
        IRSwap(0.0, 3.0, 0.035),     # 0-3Y (overlaps with first)
        IRSwap(1.0, 3.0, 0.038),     # 1-3Y (overlaps with both)
        IRSwap(2.0, 4.0, 0.040),     # 2-4Y (overlaps)
        IRSwap(1.5, 3.5, 0.039),     # 1.5-3.5Y (heavy overlap)
    ]
    
    market_prices = [0.0, 0.0, 0.0, 0.0, 0.0]
    
    print(f"\n📊 Over-determined System:")
    print(f"  {len(instruments)} instruments trying to determine ~4 curve points")
    
    for i, inst in enumerate(instruments):
        print(f"  {i+1}. {inst}")
    
    bootstrapper = CurveBootstrapper(interpolation_method='linear')
    
    try:
        curve = bootstrapper.bootstrap_with_forward_control(instruments, market_prices)
        
        print(f"\n✅ Bootstrapping succeeded (optimization found best fit)")
        print(f"   Curve points: {len(curve.tenors)}")
        
        # Check how well each instrument is priced
        print(f"\n🔍 Instrument Pricing Check:")
        total_error = 0
        for i, inst in enumerate(instruments):
            price = inst.price(curve)
            error = abs(price - market_prices[i])
            total_error += error
            print(f"  {inst}: Price = {price:>8.6f}, Target = {market_prices[i]:.6f}, Error = {error:.6f}")
        
        print(f"\n📈 Total Absolute Error: {total_error:.6f}")
        print(f"   Average Error per Instrument: {total_error/len(instruments):.6f}")
        
        return curve, total_error
        
    except Exception as e:
        print(f"\n❌ Bootstrapping failed: {e}")
        return None, float('inf')


def demonstrate_underdetermination():
    """Demonstrate under-determined systems with gaps."""
    
    print("\n" + "=" * 70)
    print("UNDER-DETERMINATION ANALYSIS")
    print("=" * 70)
    
    print("\n🎯 Creating system with gaps in coverage")
    
    # Create instruments with gaps
    instruments = [
        IRSwap(0.0, 1.0, 0.025),     # 0-1Y
        IRSwap(3.0, 5.0, 0.040),     # 3-5Y (gap from 1-3Y)
        IRSwap(7.0, 10.0, 0.045),    # 7-10Y (gap from 5-7Y)
    ]
    
    market_prices = [0.0, 0.0, 0.0]
    
    print(f"\n📊 Under-determined System with Gaps:")
    for i, inst in enumerate(instruments):
        print(f"  {i+1}. {inst}")
    
    print(f"\n⚠️  Coverage Gaps:")
    print(f"  1.0Y - 3.0Y: No direct control")
    print(f"  5.0Y - 7.0Y: No direct control")
    
    bootstrapper = CurveBootstrapper(interpolation_method='cubic')
    
    try:
        curve = bootstrapper.bootstrap_with_forward_control(instruments, market_prices)
        
        print(f"\n✅ Bootstrapping succeeded with interpolation filling gaps")
        
        # Show rates in gap regions
        print(f"\n📈 Rates in Gap Regions (interpolated):")
        gap_tenors = [1.5, 2.0, 2.5, 5.5, 6.0, 6.5]
        for tenor in gap_tenors:
            rate = curve.get_rate(tenor)
            print(f"  {tenor:.1f}Y: {rate:.4%}")
        
        return curve
        
    except Exception as e:
        print(f"\n❌ Bootstrapping failed: {e}")
        return None


def analyze_sensitivity_with_overlaps():
    """Analyze how overlapping swaps affect sensitivity."""
    
    print("\n" + "=" * 70)
    print("SENSITIVITY ANALYSIS WITH OVERLAPS")
    print("=" * 70)
    
    # Create a base curve
    tenors = [1.0, 2.0, 3.0, 5.0, 7.0, 10.0]
    rates = [0.025, 0.03, 0.035, 0.04, 0.042, 0.045]
    curve = YieldCurve(tenors, rates, interpolation_method='cubic')
    
    # Create overlapping swaps
    swaps = [
        IRSwap(1.0, 4.0, 0.035),    # 1-4Y
        IRSwap(2.0, 5.0, 0.040),    # 2-5Y (overlaps 2-4Y)
        IRSwap(3.0, 6.0, 0.042),    # 3-6Y (overlaps 3-5Y)
    ]
    
    print(f"\n📊 Overlapping Swaps Sensitivity Analysis:")
    
    # Test sensitivity to rate shocks in different regions
    rate_segments = [
        (1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 5.0), (5.0, 6.0)
    ]
    
    print(f"\n{'Swap':<25} {'Segment':<10} {'Sensitivity':<12} {'Overlap Impact'}")
    print("-" * 75)
    
    for swap in swaps:
        print(f"\n{str(swap):<25}")
        
        for start_seg, end_seg in rate_segments:
            sensitivity = swap.get_forward_rate_sensitivity(curve, start_seg, end_seg)
            
            # Check how many other swaps also affect this segment
            other_affected = []
            for other_swap in swaps:
                if other_swap != swap:
                    other_sens = other_swap.get_forward_rate_sensitivity(curve, start_seg, end_seg)
                    if other_sens > 1e-6:
                        other_affected.append(str(other_swap))
            
            overlap_info = f"{len(other_affected)} others" if other_affected else "No overlap"
            
            print(f"{'':25} {start_seg}-{end_seg}Y     {sensitivity:>10.6f}  {overlap_info}")


def demonstrate_best_practices():
    """Demonstrate best practices for handling overlapping swaps."""
    
    print("\n" + "=" * 70)
    print("BEST PRACTICES FOR OVERLAPPING SWAPS")
    print("=" * 70)
    
    print(f"\n🎯 Recommended Approaches:")
    
    print(f"\n1. 📐 NON-OVERLAPPING PARTITION:")
    print(f"   Use swaps that partition the curve without overlap")
    
    non_overlap = [
        IRSwap(0.0, 2.0, 0.030),     # 0-2Y
        IRSwap(2.0, 5.0, 0.035),     # 2-5Y (starts where previous ends)
        IRSwap(5.0, 10.0, 0.040),    # 5-10Y (starts where previous ends)
    ]
    
    for swap in non_overlap:
        print(f"     {swap}")
    
    print(f"\n2. 🎚️  HIERARCHICAL APPROACH:")
    print(f"   Use spot swaps for anchoring + forward swaps for specific segments")
    
    hierarchical = [
        IRSwap(0.0, 1.0, 0.025),     # 1Y anchor
        IRSwap(0.0, 2.0, 0.030),     # 2Y anchor
        IRSwap(2.0, 5.0, 0.035),     # 2-5Y segment control
        IRSwap(5.0, 10.0, 0.040),    # 5-10Y segment control
    ]
    
    for swap in hierarchical:
        print(f"     {swap}")
    
    print(f"\n3. 🎯 TARGETED CONTROL:")
    print(f"   Use forward swaps only for specific curve segments you want to control")
    
    targeted = [
        IRSwap(0.0, 5.0, 0.035),     # Main curve backbone
        IRSwap(2.0, 3.0, 0.032),     # Target specific 2-3Y segment
        IRSwap(7.0, 10.0, 0.042),    # Target long-end segment
    ]
    
    for swap in targeted:
        print(f"     {swap}")
    
    print(f"\n⚠️  Issues with Heavy Overlap:")
    print(f"   • Over-determination: More constraints than degrees of freedom")
    print(f"   • Inconsistent pricing: Conflicting market signals")
    print(f"   • Numerical instability: Optimization may struggle")
    print(f"   • Unclear sensitivity: Multiple instruments affect same rates")
    
    print(f"\n✅ When Overlap is Acceptable:")
    print(f"   • Market-making: Multiple liquid instruments for same period")
    print(f"   • Risk management: Hedging specific exposures")
    print(f"   • Arbitrage: Exploiting pricing inconsistencies")
    print(f"   • Robustness: Cross-validation of curve construction")


def visualize_overlap_impact():
    """Visualize the impact of overlapping vs non-overlapping swaps."""
    
    print(f"\n📊 Creating visualization of overlap impact...")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Scenario 1: Non-overlapping swaps
    non_overlap_swaps = [
        IRSwap(0.0, 2.0, 0.030),
        IRSwap(2.0, 5.0, 0.035),
        IRSwap(5.0, 10.0, 0.040),
    ]
    
    # Scenario 2: Overlapping swaps
    overlap_swaps = [
        IRSwap(0.0, 3.0, 0.032),
        IRSwap(1.0, 4.0, 0.035),
        IRSwap(2.0, 6.0, 0.038),
        IRSwap(4.0, 8.0, 0.041),
        IRSwap(6.0, 10.0, 0.043),
    ]
    
    # Plot coverage for non-overlapping
    ax1.set_title("Non-Overlapping Forward Swaps (Clean Partition)")
    for i, swap in enumerate(non_overlap_swaps):
        ax1.barh(i, swap.maturity - swap.start_date, left=swap.start_date, 
                height=0.6, alpha=0.7, label=f"{swap}")
        ax1.text((swap.start_date + swap.maturity) / 2, i, 
                f"{swap.start_date}Y-{swap.maturity}Y", 
                ha='center', va='center', fontweight='bold')
    
    ax1.set_xlabel('Tenor (Years)')
    ax1.set_ylabel('Instruments')
    ax1.set_yticks(range(len(non_overlap_swaps)))
    ax1.set_yticklabels([f"Swap {i+1}" for i in range(len(non_overlap_swaps))])
    ax1.grid(True, alpha=0.3, axis='x')
    ax1.set_xlim(0, 10)
    
    # Plot coverage for overlapping
    ax2.set_title("Overlapping Forward Swaps (Over-determined System)")
    colors = ['red', 'blue', 'green', 'orange', 'purple']
    for i, swap in enumerate(overlap_swaps):
        ax2.barh(i, swap.maturity - swap.start_date, left=swap.start_date, 
                height=0.6, alpha=0.6, color=colors[i % len(colors)], 
                label=f"{swap}")
        ax2.text((swap.start_date + swap.maturity) / 2, i, 
                f"{swap.start_date}Y-{swap.maturity}Y", 
                ha='center', va='center', fontweight='bold', fontsize=8)
    
    ax2.set_xlabel('Tenor (Years)')
    ax2.set_ylabel('Instruments')
    ax2.set_yticks(range(len(overlap_swaps)))
    ax2.set_yticklabels([f"Swap {i+1}" for i in range(len(overlap_swaps))])
    ax2.grid(True, alpha=0.3, axis='x')
    ax2.set_xlim(0, 10)
    
    # Add overlap highlighting
    overlap_regions = [(1, 3), (2, 4), (4, 6), (6, 8)]
    for start, end in overlap_regions:
        ax2.axvspan(start, end, alpha=0.2, color='red')
    
    plt.tight_layout()
    plt.savefig('overlap_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"📊 Overlap visualization saved as 'overlap_analysis.png'")


def main():
    """Run all overlap analysis demonstrations."""
    
    print("🔄 FORWARD STARTING SWAP OVERLAP ANALYSIS")
    print("==========================================")
    print("Understanding what happens when forward starting swaps overlap")
    
    try:
        # Run all analyses
        instruments, overlaps = analyze_overlapping_swaps()
        curve1, error1 = demonstrate_overdetermination()
        curve2 = demonstrate_underdetermination()
        analyze_sensitivity_with_overlaps()
        demonstrate_best_practices()
        visualize_overlap_impact()
        
        print("\n" + "=" * 70)
        print("🎉 OVERLAP ANALYSIS COMPLETED!")
        print("=" * 70)
        
        print(f"\n✨ Key Insights:")
        print(f"• Overlapping swaps create over-determined systems")
        print(f"• Optimization finds best fit but may not price all instruments to zero")
        print(f"• Non-overlapping partitions provide cleaner curve control")
        print(f"• Gaps require interpolation to fill missing curve segments")
        print(f"• Market reality often involves overlaps - handle with care!")
        
        print(f"\n🎯 Recommendations:")
        print(f"• Use non-overlapping partitions when possible")
        print(f"• If overlaps exist, expect small pricing errors")
        print(f"• Monitor total fitting error across all instruments")
        print(f"• Consider hierarchical approach for complex curves")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 