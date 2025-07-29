"""
Unit tests for the flat interpolation method.
"""

import unittest
import numpy as np
from src.core.curve import YieldCurve


class TestFlatInterpolation(unittest.TestCase):
    """Test cases for flat interpolation method."""
    
    def setUp(self):
        """Set up test data."""
        # FOMC-style rate curve
        self.fomc_dates = [0.25, 0.5, 1.0, 2.0, 5.0]
        self.fed_rates = [0.05, 0.0525, 0.055, 0.06, 0.065]
        self.flat_curve = YieldCurve(self.fomc_dates, self.fed_rates, interpolation_method='flat')
    
    def test_flat_interpolation_at_nodes(self):
        """Test that interpolation returns exact values at known points."""
        for tenor, expected_rate in zip(self.fomc_dates, self.fed_rates):
            actual_rate = self.flat_curve.get_rate(tenor)
            self.assertAlmostEqual(actual_rate, expected_rate, places=6)
    
    def test_flat_interpolation_between_nodes(self):
        """Test that rates stay flat between nodes."""
        # Test between 0.25 and 0.5 (should be 0.05)
        test_tenor = 0.3
        expected_rate = 0.05  # Should use the previous rate
        actual_rate = self.flat_curve.get_rate(test_tenor)
        self.assertAlmostEqual(actual_rate, expected_rate, places=6)
        
        # Test between 0.5 and 1.0 (should be 0.0525)
        test_tenor = 0.75
        expected_rate = 0.0525
        actual_rate = self.flat_curve.get_rate(test_tenor)
        self.assertAlmostEqual(actual_rate, expected_rate, places=6)
        
        # Test between 1.0 and 2.0 (should be 0.055)
        test_tenor = 1.5
        expected_rate = 0.055
        actual_rate = self.flat_curve.get_rate(test_tenor)
        self.assertAlmostEqual(actual_rate, expected_rate, places=6)
    
    def test_flat_interpolation_extrapolation(self):
        """Test extrapolation behavior (should use first/last rate)."""
        # Before first point
        early_rate = self.flat_curve.get_rate(0.1)
        self.assertAlmostEqual(early_rate, self.fed_rates[0], places=6)
        
        # After last point
        late_rate = self.flat_curve.get_rate(10.0)
        self.assertAlmostEqual(late_rate, self.fed_rates[-1], places=6)
    
    def test_flat_vs_other_interpolation_methods(self):
        """Compare flat interpolation with other methods."""
        linear_curve = YieldCurve(self.fomc_dates, self.fed_rates, interpolation_method='linear')
        cubic_curve = YieldCurve(self.fomc_dates, self.fed_rates, interpolation_method='cubic')
        
        # Test at a point between nodes where they should differ
        test_tenor = 0.75
        
        flat_rate = self.flat_curve.get_rate(test_tenor)
        linear_rate = linear_curve.get_rate(test_tenor)
        cubic_rate = cubic_curve.get_rate(test_tenor)
        
        # Flat should equal the previous node (0.0525)
        self.assertAlmostEqual(flat_rate, 0.0525, places=6)
        
        # Linear and cubic should be different from flat
        self.assertNotAlmostEqual(flat_rate, linear_rate, places=3)
        self.assertNotAlmostEqual(flat_rate, cubic_rate, places=3)
    
    def test_flat_interpolation_step_function(self):
        """Test that flat interpolation creates proper step function."""
        # Create a detailed test across the entire curve
        test_tenors = np.linspace(0.1, 6.0, 100)
        rates = [self.flat_curve.get_rate(t) for t in test_tenors]
        
        # Verify step function behavior
        for i, tenor in enumerate(test_tenors):
            rate = rates[i]
            
            if tenor <= 0.25:
                expected = 0.05
            elif tenor <= 0.5:
                expected = 0.05
            elif tenor <= 1.0:
                expected = 0.0525
            elif tenor <= 2.0:
                expected = 0.055
            elif tenor <= 5.0:
                expected = 0.06
            else:
                expected = 0.065
            
            self.assertAlmostEqual(rate, expected, places=6, 
                                 msg=f"Failed at tenor {tenor}")
    
    def test_flat_interpolation_with_different_curves(self):
        """Test flat interpolation with different curve shapes."""
        test_cases = [
            # Flat curve
            ([0.5, 1.0, 2.0], [0.03, 0.03, 0.03]),
            # Rising curve
            ([0.5, 1.0, 2.0], [0.02, 0.04, 0.06]),
            # Falling curve
            ([0.5, 1.0, 2.0], [0.06, 0.04, 0.02]),
            # Volatile curve
            ([0.5, 1.0, 2.0], [0.02, 0.08, 0.03])
        ]
        
        for tenors, rates in test_cases:
            with self.subTest(tenors=tenors, rates=rates):
                curve = YieldCurve(tenors, rates, interpolation_method='flat')
                
                # Test that exact points return exact rates
                for tenor, rate in zip(tenors, rates):
                    actual = curve.get_rate(tenor)
                    self.assertAlmostEqual(actual, rate, places=6)
                
                # Test intermediate points
                if len(tenors) > 1:
                    mid_tenor = (tenors[0] + tenors[1]) / 2
                    mid_rate = curve.get_rate(mid_tenor)
                    # Should equal the first rate (step function)
                    self.assertAlmostEqual(mid_rate, rates[0], places=6)
    
    def test_flat_interpolation_discount_factors(self):
        """Test that discount factors work correctly with flat interpolation."""
        # Test discount factor calculation
        for tenor in [0.3, 0.75, 1.5, 3.0]:
            rate = self.flat_curve.get_rate(tenor)
            df = self.flat_curve.get_discount_factor(tenor)
            expected_df = np.exp(-rate * tenor)
            
            self.assertAlmostEqual(df, expected_df, places=6)
            self.assertGreater(df, 0)  # Should be positive
            self.assertLessEqual(df, 1)  # Should be <= 1
    
    def test_flat_interpolation_forward_rates(self):
        """Test forward rate calculation with flat interpolation."""
        # Test forward rates between different periods
        start_tenor = 0.5
        end_tenor = 1.0
        
        forward_rate = self.flat_curve.get_forward_rate(start_tenor, end_tenor)
        
        # Should be finite and positive
        self.assertTrue(np.isfinite(forward_rate))
        self.assertGreater(forward_rate, 0)


if __name__ == '__main__':
    unittest.main() 