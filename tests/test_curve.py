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