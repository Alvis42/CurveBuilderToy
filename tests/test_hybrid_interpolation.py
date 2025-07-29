"""
Unit tests for the hybrid interpolation method.
"""

import unittest
import numpy as np
from src.core.curve import YieldCurve


class TestHybridInterpolation(unittest.TestCase):
    """Test cases for hybrid interpolation method."""
    
    def setUp(self):
        """Set up test data."""
        self.tenors = [0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
        self.rates = [0.05, 0.0525, 0.055, 0.06, 0.062, 0.065]
        self.cutoff_tenor = 2.0
    
    def test_hybrid_interpolation_basic(self):
        """Test basic hybrid interpolation functionality."""
        curve = YieldCurve(self.tenors, self.rates,
                          interpolation_method='hybrid',
                          cutoff_tenor=self.cutoff_tenor,
                          pre_cutoff_method='flat',
                          post_cutoff_method='cubic')
        
        # Test at known points
        for tenor, expected_rate in zip(self.tenors, self.rates):
            actual_rate = curve.get_rate(tenor)
            self.assertAlmostEqual(actual_rate, expected_rate, places=5)
    
    def test_hybrid_pre_cutoff_behavior(self):
        """Test that pre-cutoff uses flat interpolation."""
        curve = YieldCurve(self.tenors, self.rates,
                          interpolation_method='hybrid',
                          cutoff_tenor=self.cutoff_tenor,
                          pre_cutoff_method='flat',
                          post_cutoff_method='cubic')
        
        # Test between 0.5 and 1.0 (should use flat = 0.0525)
        test_tenor = 0.75
        rate = curve.get_rate(test_tenor)
        self.assertAlmostEqual(rate, 0.0525, places=6)
        
        # Test between 1.0 and 2.0 (should use flat = 0.055)
        test_tenor = 1.5
        rate = curve.get_rate(test_tenor)
        self.assertAlmostEqual(rate, 0.055, places=6)
    
    def test_hybrid_post_cutoff_behavior(self):
        """Test that post-cutoff uses cubic interpolation."""
        curve = YieldCurve(self.tenors, self.rates,
                          interpolation_method='hybrid',
                          cutoff_tenor=self.cutoff_tenor,
                          pre_cutoff_method='flat',
                          post_cutoff_method='cubic')
        
        # Create pure cubic curve for comparison
        post_cutoff_tenors = [t for t in self.tenors if t >= self.cutoff_tenor]
        post_cutoff_rates = [r for t, r in zip(self.tenors, self.rates) if t >= self.cutoff_tenor]
        cubic_curve = YieldCurve(post_cutoff_tenors, post_cutoff_rates, interpolation_method='cubic')
        
        # Test a point after cutoff
        test_tenor = 7.0
        hybrid_rate = curve.get_rate(test_tenor)
        cubic_rate = cubic_curve.get_rate(test_tenor)
        
        # Should be very close (small differences due to implementation)
        self.assertAlmostEqual(hybrid_rate, cubic_rate, places=3)
    
    def test_hybrid_cutoff_transition(self):
        """Test smooth transition at cutoff point."""
        curve = YieldCurve(self.tenors, self.rates,
                          interpolation_method='hybrid',
                          cutoff_tenor=self.cutoff_tenor,
                          pre_cutoff_method='flat',
                          post_cutoff_method='cubic')
        
        # Test very close to cutoff from both sides
        just_before = curve.get_rate(self.cutoff_tenor - 0.001)
        just_after = curve.get_rate(self.cutoff_tenor + 0.001)
        at_cutoff = curve.get_rate(self.cutoff_tenor)
        
        # All should be close (transition should be smooth)
        self.assertAlmostEqual(just_before, at_cutoff, places=2)
        self.assertAlmostEqual(just_after, at_cutoff, places=2)
    
    def test_hybrid_different_method_combinations(self):
        """Test different combinations of pre/post cutoff methods."""
        combinations = [
            ('flat', 'linear'),
            ('linear', 'cubic'),
            ('flat', 'cubic'),
        ]
        
        for pre_method, post_method in combinations:
            with self.subTest(pre=pre_method, post=post_method):
                curve = YieldCurve(self.tenors, self.rates,
                                  interpolation_method='hybrid',
                                  cutoff_tenor=self.cutoff_tenor,
                                  pre_cutoff_method=pre_method,
                                  post_cutoff_method=post_method)
                
                # Test that it works without errors
                test_tenors = [0.3, 1.5, 3.0, 8.0]
                for tenor in test_tenors:
                    rate = curve.get_rate(tenor)
                    self.assertTrue(np.isfinite(rate))
                    self.assertGreater(rate, 0)
    
    def test_hybrid_different_cutoff_points(self):
        """Test hybrid interpolation with different cutoff points."""
        cutoff_points = [0.5, 1.0, 2.0, 5.0]
        
        for cutoff in cutoff_points:
            with self.subTest(cutoff=cutoff):
                curve = YieldCurve(self.tenors, self.rates,
                                  interpolation_method='hybrid',
                                  cutoff_tenor=cutoff,
                                  pre_cutoff_method='flat',
                                  post_cutoff_method='cubic')
                
                # Test various points
                test_tenors = [0.1, 0.75, 1.5, 3.0, 7.0]
                for tenor in test_tenors:
                    rate = curve.get_rate(tenor)
                    self.assertTrue(np.isfinite(rate))
                    self.assertGreater(rate, 0)
    
    def test_hybrid_cutoff_not_in_data(self):
        """Test hybrid interpolation when cutoff point is not in original data."""
        cutoff_tenor = 1.5  # Between 1.0 and 2.0
        
        curve = YieldCurve(self.tenors, self.rates,
                          interpolation_method='hybrid',
                          cutoff_tenor=cutoff_tenor,
                          pre_cutoff_method='flat',
                          post_cutoff_method='cubic')
        
        # Should work fine and interpolate cutoff rate
        rate_at_cutoff = curve.get_rate(cutoff_tenor)
        self.assertTrue(np.isfinite(rate_at_cutoff))
        self.assertGreater(rate_at_cutoff, 0)
        
        # Test points on both sides
        before_cutoff = curve.get_rate(1.2)  # Should use flat
        after_cutoff = curve.get_rate(1.8)   # Should use cubic
        
        self.assertTrue(np.isfinite(before_cutoff))
        self.assertTrue(np.isfinite(after_cutoff))
    
    def test_hybrid_extreme_cutoff_points(self):
        """Test hybrid interpolation with extreme cutoff points."""
        # Cutoff before all data points
        curve1 = YieldCurve(self.tenors, self.rates,
                           interpolation_method='hybrid',
                           cutoff_tenor=0.1,
                           pre_cutoff_method='flat',
                           post_cutoff_method='cubic')
        
        rate1 = curve1.get_rate(1.0)
        self.assertTrue(np.isfinite(rate1))
        
        # Cutoff after all data points
        curve2 = YieldCurve(self.tenors, self.rates,
                           interpolation_method='hybrid',
                           cutoff_tenor=20.0,
                           pre_cutoff_method='flat',
                           post_cutoff_method='cubic')
        
        rate2 = curve2.get_rate(5.0)
        self.assertTrue(np.isfinite(rate2))
    
    def test_hybrid_vs_pure_methods(self):
        """Compare hybrid interpolation with pure methods."""
        hybrid_curve = YieldCurve(self.tenors, self.rates,
                                 interpolation_method='hybrid',
                                 cutoff_tenor=self.cutoff_tenor,
                                 pre_cutoff_method='flat',
                                 post_cutoff_method='cubic')
        
        flat_curve = YieldCurve(self.tenors, self.rates, interpolation_method='flat')
        cubic_curve = YieldCurve(self.tenors, self.rates, interpolation_method='cubic')
        
        # Before cutoff: hybrid should match flat for intermediate points
        test_tenor = 0.75
        hybrid_rate = hybrid_curve.get_rate(test_tenor)
        flat_rate = flat_curve.get_rate(test_tenor)
        
        self.assertAlmostEqual(hybrid_rate, flat_rate, places=6)
        
        # After cutoff: hybrid should be different from flat
        test_tenor = 7.0
        hybrid_rate = hybrid_curve.get_rate(test_tenor)
        cubic_rate = cubic_curve.get_rate(test_tenor)
        flat_rate = flat_curve.get_rate(test_tenor)
        
        # Hybrid should be different from flat (but similar to cubic)
        self.assertNotAlmostEqual(hybrid_rate, flat_rate, places=3)
        self.assertTrue(np.isfinite(hybrid_rate))
        self.assertTrue(np.isfinite(cubic_rate))
    
    def test_hybrid_discount_factors(self):
        """Test discount factor calculation with hybrid interpolation."""
        curve = YieldCurve(self.tenors, self.rates,
                          interpolation_method='hybrid',
                          cutoff_tenor=self.cutoff_tenor,
                          pre_cutoff_method='flat',
                          post_cutoff_method='cubic')
        
        # Test discount factors at various points
        test_tenors = [0.3, 1.5, 3.0, 8.0]
        for tenor in test_tenors:
            rate = curve.get_rate(tenor)
            df = curve.get_discount_factor(tenor)
            expected_df = np.exp(-rate * tenor)
            
            self.assertAlmostEqual(df, expected_df, places=6)
            self.assertGreater(df, 0)
            self.assertLessEqual(df, 1)
    
    def test_hybrid_forward_rates(self):
        """Test forward rate calculation with hybrid interpolation."""
        curve = YieldCurve(self.tenors, self.rates,
                          interpolation_method='hybrid',
                          cutoff_tenor=self.cutoff_tenor,
                          pre_cutoff_method='flat',
                          post_cutoff_method='cubic')
        
        # Test forward rates across cutoff boundary
        forward_rate = curve.get_forward_rate(1.0, 3.0)
        
        self.assertTrue(np.isfinite(forward_rate))
        self.assertGreater(forward_rate, 0)
    
    def test_hybrid_error_handling(self):
        """Test error handling for hybrid interpolation."""
        # Test missing cutoff_tenor
        with self.assertRaises(ValueError):
            YieldCurve(self.tenors, self.rates,
                      interpolation_method='hybrid')
        
        # Test invalid methods
        with self.assertRaises(ValueError):
            YieldCurve(self.tenors, self.rates,
                      interpolation_method='hybrid',
                      cutoff_tenor=2.0,
                      pre_cutoff_method='invalid',
                      post_cutoff_method='cubic')


if __name__ == '__main__':
    unittest.main() 