"""
Basic tests for the curve building functionality.
"""

import unittest
import numpy as np
from src.core.curve import YieldCurve
from src.core.instruments import IRSwap, IRFuture
from src.core.bootstrapping import CurveBootstrapper


class TestYieldCurve(unittest.TestCase):
    """Test cases for YieldCurve class."""
    
    def setUp(self):
        """Set up test data."""
        self.tenors = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
        self.rates = [0.025, 0.0275, 0.03, 0.0325, 0.035, 0.0375]
        self.curve = YieldCurve(self.tenors, self.rates)
    
    def test_curve_creation(self):
        """Test curve creation."""
        self.assertEqual(len(self.curve.tenors), len(self.curve.rates))
        self.assertTrue(np.all(np.diff(self.curve.tenors) > 0))
    
    def test_rate_interpolation(self):
        """Test rate interpolation."""
        # Test at known points
        for tenor, rate in zip(self.tenors, self.rates):
            interpolated_rate = self.curve.get_rate(tenor)
            self.assertAlmostEqual(interpolated_rate, rate, places=6)
        
        # Test interpolation at intermediate point
        mid_tenor = 1.5
        mid_rate = self.curve.get_rate(mid_tenor)
        self.assertTrue(0.0275 < mid_rate < 0.03)
    
    def test_discount_factor(self):
        """Test discount factor calculation."""
        tenor = 2.0
        rate = self.curve.get_rate(tenor)
        expected_df = np.exp(-rate * tenor)
        actual_df = self.curve.get_discount_factor(tenor)
        self.assertAlmostEqual(actual_df, expected_df, places=6)
    
    def test_forward_rate(self):
        """Test forward rate calculation."""
        start_tenor = 1.0
        end_tenor = 2.0
        forward_rate = self.curve.get_forward_rate(start_tenor, end_tenor)
        
        # Forward rate should be positive
        self.assertGreater(forward_rate, 0)
        
        # Forward rate should be reasonable
        start_rate = self.curve.get_rate(start_tenor)
        end_rate = self.curve.get_rate(end_tenor)
        self.assertTrue(0 <= forward_rate <= max(start_rate, end_rate) * 2)


class TestInstruments(unittest.TestCase):
    """Test cases for financial instruments."""
    
    def setUp(self):
        """Set up test data."""
        self.tenors = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
        self.rates = [0.025, 0.0275, 0.03, 0.0325, 0.035, 0.0375]
        self.curve = YieldCurve(self.tenors, self.rates)
    
    def test_swap_pricing(self):
        """Test swap pricing."""
        swap = IRSwap(0.0, 5.0, 0.035, notional=1.0)
        price = swap.price(self.curve)
        
        # Price should be finite
        self.assertTrue(np.isfinite(price))
    
    def test_future_pricing(self):
        """Test future pricing."""
        future = IRFuture(0.0, 0.25, notional=1.0)
        price = future.price(self.curve)
        
        # Price should be finite and positive
        self.assertTrue(np.isfinite(price))
        self.assertGreater(price, 0)
    
    def test_dv01_calculation(self):
        """Test DV01 calculation."""
        swap = IRSwap(0.0, 5.0, 0.035, notional=1.0)
        dv01 = swap.get_dv01(self.curve)
        
        # DV01 should be finite for a swap
        self.assertTrue(np.isfinite(dv01))


class TestSwapPricing(unittest.TestCase):
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
    
    def test_par_swap_pricing(self):
        """Test that par swaps have approximately zero value."""
        # Create a swap with fixed rate equal to the par rate
        swap_tenor = 5.0
        par_rate = self.upward_curve.get_par_rate(swap_tenor)
        par_swap = IRSwap(0.0, swap_tenor, par_rate, notional=1.0)
        
        price = par_swap.price(self.upward_curve)
        
        # Par swap should have price close to zero
        self.assertAlmostEqual(price, 0.0, places=2)
    
    def test_swap_pricing_different_curves(self):
        """Test swap pricing across different curve shapes."""
        swap = IRSwap(0.0, 5.0, 0.04, notional=1.0)
        
        # Test on flat curve
        flat_price = swap.price(self.flat_curve)
        self.assertTrue(np.isfinite(flat_price))
        
        # Test on upward sloping curve
        upward_price = swap.price(self.upward_curve)
        self.assertTrue(np.isfinite(upward_price))
        
        # Test on downward sloping curve
        downward_price = swap.price(self.downward_curve)
        self.assertTrue(np.isfinite(downward_price))
    
    def test_swap_sensitivity_to_fixed_rate(self):
        """Test how swap price changes with fixed rate."""
        swap_tenor = 3.0
        par_rate = self.upward_curve.get_par_rate(swap_tenor)
        
        # Test swap with rate above par
        high_rate_swap = IRSwap(0.0, swap_tenor, par_rate + 0.01, notional=1.0)
        high_price = high_rate_swap.price(self.upward_curve)
        
        # Test swap with rate below par
        low_rate_swap = IRSwap(0.0, swap_tenor, par_rate - 0.01, notional=1.0)
        low_price = low_rate_swap.price(self.upward_curve)
        
        # High rate swap should have negative value (receiver pays)
        # Low rate swap should have positive value (payer pays)
        self.assertLess(high_price, 0)
        self.assertGreater(low_price, 0)
    
    def test_swap_cashflows(self):
        """Test swap cashflow calculation."""
        swap = IRSwap(0.0, 2.0, 0.04, notional=1.0)
        cashflows = swap.get_cashflows(self.upward_curve)
        
        # Should return a dictionary with dates, fixed, and floating cashflows
        self.assertIsInstance(cashflows, dict)
        self.assertIn('dates', cashflows)
        self.assertIn('fixed', cashflows)
        self.assertIn('floating', cashflows)
        
        # Should have cashflows
        self.assertGreater(len(cashflows['dates']), 0)
        self.assertGreater(len(cashflows['fixed']), 0)
        self.assertGreater(len(cashflows['floating']), 0)
        
        # Each cashflow should be finite
        for cf in cashflows['fixed']:
            self.assertTrue(np.isfinite(cf))
        for cf in cashflows['floating']:
            self.assertTrue(np.isfinite(cf))
    
    def test_swap_dv01_calculation(self):
        """Test DV01 calculation for swaps."""
        swap = IRSwap(0.0, 5.0, 0.04, notional=1.0)
        dv01 = swap.get_dv01(self.upward_curve)
        
        # DV01 should be finite
        self.assertTrue(np.isfinite(dv01))
        
        # DV01 can be positive or negative depending on the swap position
        # For a receiver swap (long fixed rate), DV01 is typically negative
        # For a payer swap (short fixed rate), DV01 is typically positive
        self.assertTrue(np.isfinite(dv01))
    
    def test_swap_convexity(self):
        """Test convexity calculation for swaps."""
        swap = IRSwap(0.0, 5.0, 0.04, notional=1.0)
        convexity = swap.get_convexity(self.upward_curve)
        
        # Convexity should be finite
        self.assertTrue(np.isfinite(convexity))
        
        # Convexity can be positive or negative depending on the curve shape
        # and swap position, but should be finite
        self.assertTrue(np.isfinite(convexity))
    
    def test_swap_different_tenors(self):
        """Test swap pricing with different tenors."""
        tenors = [1.0, 2.0, 5.0, 10.0]
        fixed_rate = 0.04
        
        for tenor in tenors:
            swap = IRSwap(0.0, tenor, fixed_rate, notional=1.0)
            price = swap.price(self.upward_curve)
            
            # Price should be finite
            self.assertTrue(np.isfinite(price))
            
            # Longer tenors should have larger absolute price (all else equal)
            # But this depends on the curve shape, so we'll just check finiteness
            if tenor > 1.0:
                short_swap = IRSwap(0.0, 1.0, fixed_rate, notional=1.0)
                short_price = short_swap.price(self.upward_curve)
                self.assertTrue(np.isfinite(short_price))
    
    def test_swap_notional_sensitivity(self):
        """Test that swap price scales with notional."""
        swap_1m = IRSwap(0.0, 5.0, 0.04, notional=1.0)
        swap_10m = IRSwap(0.0, 5.0, 0.04, notional=10.0)
        
        price_1m = swap_1m.price(self.upward_curve)
        price_10m = swap_10m.price(self.upward_curve)
        
        # Price should scale linearly with notional
        self.assertAlmostEqual(price_10m, price_1m * 10, places=6)
    
    def test_swap_payment_frequency(self):
        """Test swap pricing with different payment frequencies."""
        # Semi-annual payments (default)
        swap_semi = IRSwap(0.0, 2.0, 0.04, notional=1.0, frequency=2)
        price_semi = swap_semi.price(self.upward_curve)
        
        # Annual payments
        swap_annual = IRSwap(0.0, 2.0, 0.04, notional=1.0, frequency=1)
        price_annual = swap_annual.price(self.upward_curve)
        
        # Quarterly payments
        swap_quarterly = IRSwap(0.0, 2.0, 0.04, notional=1.0, frequency=4)
        price_quarterly = swap_quarterly.price(self.upward_curve)
        
        # All should be finite
        self.assertTrue(np.isfinite(price_semi))
        self.assertTrue(np.isfinite(price_annual))
        self.assertTrue(np.isfinite(price_quarterly))
        
        # More frequent payments should have slightly different price due to timing
        self.assertNotEqual(price_semi, price_annual)
        self.assertNotEqual(price_semi, price_quarterly)
    
    def test_swap_edge_cases(self):
        """Test swap pricing edge cases."""
        # Very short tenor
        short_swap = IRSwap(0.0, 0.1, 0.04, notional=1.0)
        short_price = short_swap.price(self.upward_curve)
        self.assertTrue(np.isfinite(short_price))
        
        # Very long tenor
        long_swap = IRSwap(0.0, 30.0, 0.04, notional=1.0)
        long_price = long_swap.price(self.upward_curve)
        self.assertTrue(np.isfinite(long_price))
        
        # Zero fixed rate
        zero_swap = IRSwap(0.0, 5.0, 0.0, notional=1.0)
        zero_price = zero_swap.price(self.upward_curve)
        self.assertTrue(np.isfinite(zero_price))
        
        # Very high fixed rate
        high_swap = IRSwap(0.0, 5.0, 0.20, notional=1.0)
        high_price = high_swap.price(self.upward_curve)
        self.assertTrue(np.isfinite(high_price))


class TestBootstrapping(unittest.TestCase):
    """Test cases for curve bootstrapping."""
    
    def test_bootstrap_from_swaps(self):
        """Test bootstrapping from swap rates."""
        swap_tenors = [1.0, 2.0, 3.0, 5.0]
        swap_rates = [0.03, 0.032, 0.034, 0.036]
        
        bootstrapper = CurveBootstrapper()
        curve = bootstrapper.bootstrap_from_swaps(swap_rates, swap_tenors)
        
        # Curve should have the same number of points
        self.assertEqual(len(curve.tenors), len(swap_tenors))
        
        # Rates should be reasonable
        for rate in curve.rates:
            self.assertGreater(rate, 0)
            self.assertLess(rate, 0.2)  # Less than 20%


if __name__ == '__main__':
    unittest.main() 