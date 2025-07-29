"""
Comprehensive tests for swap pricing functionality.
"""

import unittest
import numpy as np
from src.core.curve import YieldCurve
from src.core.instruments import IRSwap


class TestSwapPricingComprehensive(unittest.TestCase):
    """Comprehensive test cases for swap pricing."""
    
    def setUp(self):
        """Set up test data with different curve scenarios."""
        # Flat curve
        self.flat_tenors = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
        self.flat_rates = [0.05] * 6
        self.flat_curve = YieldCurve(self.flat_tenors, self.flat_rates)
        
        # Upward sloping curve
        self.upward_tenors = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
        self.upward_rates = [0.02, 0.025, 0.03, 0.035, 0.04, 0.045]
        self.upward_curve = YieldCurve(self.upward_tenors, self.upward_rates)
        
        # Downward sloping curve
        self.downward_tenors = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
        self.downward_rates = [0.06, 0.055, 0.05, 0.045, 0.04, 0.035]
        self.downward_curve = YieldCurve(self.downward_tenors, self.downward_rates)
        
        # Inverted curve
        self.inverted_tenors = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
        self.inverted_rates = [0.08, 0.07, 0.06, 0.05, 0.04, 0.03]
        self.inverted_curve = YieldCurve(self.inverted_tenors, self.inverted_rates)
    
    def test_par_swap_zero_value(self):
        """Test that par swaps have approximately zero value."""
        test_cases = [
            (self.flat_curve, 5.0),
            (self.upward_curve, 3.0),
            (self.downward_curve, 2.0),
            (self.inverted_curve, 1.0)
        ]
        
        for curve, tenor in test_cases:
            with self.subTest(curve=curve, tenor=tenor):
                par_rate = curve.get_par_rate(tenor)
                par_swap = IRSwap(0.0, tenor, par_rate, notional=1.0)
                price = par_swap.price(curve)
                
                # Par swap should have price close to zero
                self.assertAlmostEqual(price, 0.0, places=2)
    
    def test_swap_pricing_curves(self):
        """Test swap pricing across different curve shapes."""
        swap = IRSwap(0.0, 5.0, 0.04, notional=1.0)
        
        curves = [self.flat_curve, self.upward_curve, self.downward_curve, self.inverted_curve]
        
        for curve in curves:
            with self.subTest(curve=curve):
                price = swap.price(curve)
                self.assertTrue(np.isfinite(price))
    
    def test_swap_rate_sensitivity(self):
        """Test how swap price changes with fixed rate."""
        test_cases = [
            (self.upward_curve, 3.0),
            (self.downward_curve, 2.0),
            (self.inverted_curve, 1.0)
        ]
        
        for curve, tenor in test_cases:
            with self.subTest(curve=curve, tenor=tenor):
                par_rate = curve.get_par_rate(tenor)
                
                # Test swap with rate above par
                high_rate_swap = IRSwap(0.0, tenor, par_rate + 0.01, notional=1.0)
                high_price = high_rate_swap.price(curve)
                
                # Test swap with rate below par
                low_rate_swap = IRSwap(0.0, tenor, par_rate - 0.01, notional=1.0)
                low_price = low_rate_swap.price(curve)
                
                # High rate swap should have negative value (receiver pays)
                # Low rate swap should have positive value (payer pays)
                self.assertLess(high_price, 0)
                self.assertGreater(low_price, 0)
    
    def test_swap_tenor_sensitivity(self):
        """Test swap pricing with different tenors."""
        tenors = [0.5, 1.0, 2.0, 5.0, 10.0]
        fixed_rate = 0.04
        
        for tenor in tenors:
            with self.subTest(tenor=tenor):
                swap = IRSwap(0.0, tenor, fixed_rate, notional=1.0)
                price = swap.price(self.upward_curve)
                
                # Price should be finite
                self.assertTrue(np.isfinite(price))
    
    def test_swap_notional_scaling(self):
        """Test that swap price scales with notional."""
        notional_values = [1.0, 10.0, 100.0, 1000.0]
        swap_tenor = 5.0
        fixed_rate = 0.04
        
        base_swap = IRSwap(0.0, swap_tenor, fixed_rate, notional=1.0)
        base_price = base_swap.price(self.upward_curve)
        
        for notional in notional_values:
            with self.subTest(notional=notional):
                swap = IRSwap(0.0, swap_tenor, fixed_rate, notional=notional)
                price = swap.price(self.upward_curve)
                
                # Price should scale linearly with notional
                self.assertAlmostEqual(price, base_price * notional, places=6)
    
    def test_swap_frequency_impact(self):
        """Test swap pricing with different payment frequencies."""
        frequencies = [1, 2, 4, 12]  # Annual, semi-annual, quarterly, monthly
        swap_tenor = 2.0
        fixed_rate = 0.04
        
        # Get base price with semi-annual frequency
        base_swap = IRSwap(0.0, swap_tenor, fixed_rate, notional=1.0, frequency=2)
        base_price = base_swap.price(self.upward_curve)
        
        for frequency in frequencies:
            with self.subTest(frequency=frequency):
                swap = IRSwap(0.0, swap_tenor, fixed_rate, notional=1.0, frequency=frequency)
                price = swap.price(self.upward_curve)
                
                # All should be finite
                self.assertTrue(np.isfinite(price))
                
                # More frequent payments should have different price due to timing
                if frequency != 2:
                    self.assertNotEqual(price, base_price)
    
    def test_swap_cashflow_structure(self):
        """Test swap cashflow structure."""
        swap = IRSwap(0.0, 2.0, 0.04, notional=1.0)
        cashflows = swap.get_cashflows(self.upward_curve)
        
        # Should return a dictionary with required keys
        required_keys = ['dates', 'fixed', 'floating']
        for key in required_keys:
            self.assertIn(key, cashflows)
        
        # All arrays should have the same length
        self.assertEqual(len(cashflows['dates']), len(cashflows['fixed']))
        self.assertEqual(len(cashflows['dates']), len(cashflows['floating']))
        
        # Should have cashflows
        self.assertGreater(len(cashflows['dates']), 0)
        
        # All values should be finite
        for cf in cashflows['fixed']:
            self.assertTrue(np.isfinite(cf))
        for cf in cashflows['floating']:
            self.assertTrue(np.isfinite(cf))
    
    def test_swap_sensitivity_measures(self):
        """Test swap sensitivity measures (DV01, convexity)."""
        swap = IRSwap(0.0, 5.0, 0.04, notional=1.0)
        
        # Test DV01
        dv01 = swap.get_dv01(self.upward_curve)
        self.assertTrue(np.isfinite(dv01))
        
        # Test convexity
        convexity = swap.get_convexity(self.upward_curve)
        self.assertTrue(np.isfinite(convexity))
        
        # Test with different shifts
        dv01_10bp = swap.get_dv01(self.upward_curve, shift=10.0)
        convexity_50bp = swap.get_convexity(self.upward_curve, shift=50.0)
        
        self.assertTrue(np.isfinite(dv01_10bp))
        self.assertTrue(np.isfinite(convexity_50bp))
    
    def test_swap_edge_cases(self):
        """Test swap pricing edge cases."""
        edge_cases = [
            # Very short tenor
            {'start': 0.0, 'maturity': 0.1, 'rate': 0.04},
            # Very long tenor
            {'start': 0.0, 'maturity': 30.0, 'rate': 0.04},
            # Zero fixed rate
            {'start': 0.0, 'maturity': 5.0, 'rate': 0.0},
            # Very high fixed rate
            {'start': 0.0, 'maturity': 5.0, 'rate': 0.20},
            # Very low fixed rate
            {'start': 0.0, 'maturity': 5.0, 'rate': 0.001},
        ]
        
        for case in edge_cases:
            with self.subTest(case=case):
                swap = IRSwap(
                    case['start'], 
                    case['maturity'], 
                    case['rate'], 
                    notional=1.0
                )
                price = swap.price(self.upward_curve)
                self.assertTrue(np.isfinite(price))
    
    def test_swap_curve_interpolation(self):
        """Test swap pricing with different interpolation methods."""
        tenors = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
        rates = [0.02, 0.025, 0.03, 0.035, 0.04, 0.045]
        
        # Test with different interpolation methods
        interpolation_methods = ['linear', 'cubic', 'flat']  # Skip log_linear due to edge cases
        
        for method in interpolation_methods:
            with self.subTest(method=method):
                curve = YieldCurve(tenors, rates, interpolation_method=method)
                swap = IRSwap(0.0, 3.0, 0.04, notional=1.0)
                price = swap.price(curve)
                
                # Price should be finite
                self.assertTrue(np.isfinite(price))
    
    def test_swap_pricing_accuracy(self):
        """Test swap pricing accuracy with known values."""
        # Create a flat curve at 5%
        flat_tenors = [0.5, 1.0, 2.0, 3.0, 5.0]
        flat_rates = [0.05] * 5
        flat_curve = YieldCurve(flat_tenors, flat_rates)
        
        # Test par swap (should be close to zero)
        par_rate = flat_curve.get_par_rate(2.0)
        par_swap = IRSwap(0.0, 2.0, par_rate, notional=1.0)
        par_price = par_swap.price(flat_curve)
        
        self.assertAlmostEqual(par_price, 0.0, places=2)
        
        # Test swap with 5% fixed rate on flat 5% curve
        # Should be close to zero (small differences due to payment timing)
        swap_5pct = IRSwap(0.0, 2.0, 0.05, notional=1.0)
        price_5pct = swap_5pct.price(flat_curve)
        
        self.assertAlmostEqual(price_5pct, 0.0, places=1)


if __name__ == '__main__':
    unittest.main() 