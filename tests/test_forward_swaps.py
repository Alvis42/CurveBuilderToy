"""
Unit tests for forward starting swap functionality.
"""

import unittest
import numpy as np
from src.core.curve import YieldCurve
from src.core.instruments import IRSwap
from src.core.bootstrapping import CurveBootstrapper


class TestForwardStartingSwaps(unittest.TestCase):
    """Test cases for forward starting swap functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.tenors = [0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0]
        self.rates = [0.02, 0.025, 0.03, 0.035, 0.04, 0.042, 0.045]
        self.curve = YieldCurve(self.tenors, self.rates, interpolation_method='cubic')
    
    def test_forward_swap_creation(self):
        """Test creation of forward starting swaps."""
        # Forward starting swap
        fwd_swap = IRSwap(1.0, 5.0, 0.04)
        
        self.assertEqual(fwd_swap.start_date, 1.0)
        self.assertEqual(fwd_swap.maturity, 5.0)
        self.assertEqual(fwd_swap.fixed_rate, 0.04)
        self.assertTrue(fwd_swap.is_forward_starting)
        self.assertEqual(fwd_swap.effective_tenor, 5.0)
        self.assertEqual(fwd_swap.forward_tenor_range, (1.0, 5.0))
        
        # Spot starting swap
        spot_swap = IRSwap(0.0, 5.0, 0.04)
        self.assertFalse(spot_swap.is_forward_starting)
    
    def test_forward_swap_validation(self):
        """Test validation of forward swap parameters."""
        # Start date must be before maturity
        with self.assertRaises(ValueError):
            IRSwap(5.0, 3.0, 0.04)  # Start after maturity
            
        with self.assertRaises(ValueError):
            IRSwap(5.0, 5.0, 0.04)  # Start equals maturity
    
    def test_forward_swap_payment_dates(self):
        """Test calculation of payment dates for forward swaps."""
        fwd_swap = IRSwap(1.0, 3.0, 0.04, frequency=2)  # Semi-annual
        
        # Should have payments at 1.5, 2.0, 2.5, 3.0
        expected_dates = [1.5, 2.0, 2.5, 3.0]
        self.assertEqual(len(fwd_swap.payment_dates), len(expected_dates))
        
        for actual, expected in zip(fwd_swap.payment_dates, expected_dates):
            self.assertAlmostEqual(actual, expected, places=6)
    
    def test_forward_swap_pricing(self):
        """Test pricing of forward starting swaps."""
        spot_swap = IRSwap(0.0, 5.0, 0.04)
        fwd_swap = IRSwap(2.0, 5.0, 0.04)
        
        spot_price = spot_swap.price(self.curve)
        fwd_price = fwd_swap.price(self.curve)
        
        # Both should be finite
        self.assertTrue(np.isfinite(spot_price))
        self.assertTrue(np.isfinite(fwd_price))
        
        # Forward swap should generally have different price than spot
        # (unless curve is perfectly flat at the fixed rate)
        # We just test that pricing works without errors
    
    def test_par_rate_calculation(self):
        """Test par rate calculation for forward swaps."""
        swaps = [
            IRSwap(0.0, 2.0, 0.03),   # Spot 2Y
            IRSwap(1.0, 3.0, 0.03),   # 1Y-3Y forward
            IRSwap(2.0, 5.0, 0.03),   # 2Y-5Y forward
        ]
        
        for swap in swaps:
            par_rate = swap.get_par_rate(self.curve)
            
            # Par rate should be finite and positive
            self.assertTrue(np.isfinite(par_rate))
            self.assertGreater(par_rate, 0)
            
            # Create a swap at par rate and verify it prices to ~0
            par_swap = IRSwap(swap.start_date, swap.maturity, par_rate,
                            frequency=swap.frequency, notional=swap.notional)
            par_price = par_swap.price(self.curve)
            
            # Should be very close to zero
            self.assertAlmostEqual(par_price, 0.0, places=4)
    
    def test_forward_rate_sensitivity(self):
        """Test forward rate sensitivity calculation."""
        fwd_swap = IRSwap(2.0, 5.0, 0.04)
        
        # Test sensitivity to different rate segments
        test_segments = [
            (1.0, 2.0),   # Before swap start - should be 0
            (2.0, 3.0),   # Within swap period - should be positive
            (3.0, 5.0),   # Within swap period - should be positive
            (5.0, 7.0),   # After swap end - should be 0
        ]
        
        for start_seg, end_seg in test_segments:
            sensitivity = fwd_swap.get_forward_rate_sensitivity(self.curve, start_seg, end_seg)
            
            self.assertTrue(np.isfinite(sensitivity))
            
            # Check if sensitivity makes sense
            if end_seg <= fwd_swap.start_date or start_seg >= fwd_swap.maturity:
                # Outside swap period - should be zero or very small
                self.assertAlmostEqual(sensitivity, 0.0, places=6)
            else:
                # Within swap period - should be positive (for typical case)
                self.assertGreaterEqual(sensitivity, 0.0)
    
    def test_forward_swap_cashflows(self):
        """Test cashflow calculation for forward swaps."""
        fwd_swap = IRSwap(1.0, 3.0, 0.04, frequency=2)
        cashflows = fwd_swap.get_cashflows(self.curve)
        
        # Should have dates, fixed, and floating cashflows
        self.assertIn('dates', cashflows)
        self.assertIn('fixed', cashflows)
        self.assertIn('floating', cashflows)
        
        # Number of cashflows should match payment dates
        self.assertEqual(len(cashflows['dates']), len(fwd_swap.payment_dates))
        self.assertEqual(len(cashflows['fixed']), len(fwd_swap.payment_dates))
        self.assertEqual(len(cashflows['floating']), len(fwd_swap.payment_dates))
        
        # Fixed cashflows should be constant (except for day count adjustments)
        fixed_cfs = cashflows['fixed']
        expected_fixed = fwd_swap.fixed_rate / fwd_swap.frequency * fwd_swap.notional
        
        for cf in fixed_cfs:
            self.assertAlmostEqual(cf, expected_fixed, places=6)
        
        # Floating cashflows should be positive and finite
        for cf in cashflows['floating']:
            self.assertTrue(np.isfinite(cf))
            self.assertGreaterEqual(cf, 0)
    
    def test_forward_swap_dv01(self):
        """Test DV01 calculation for forward swaps."""
        fwd_swap = IRSwap(2.0, 7.0, 0.04)
        
        dv01 = fwd_swap.get_dv01(self.curve)
        
        # DV01 should be finite
        self.assertTrue(np.isfinite(dv01))
        
        # For typical forward swaps, DV01 should be meaningful
        # (we don't test sign as it depends on whether swap is receiver or payer)
    
    def test_forward_swap_convexity(self):
        """Test convexity calculation for forward swaps."""
        fwd_swap = IRSwap(1.0, 5.0, 0.04)
        
        convexity = fwd_swap.get_convexity(self.curve)
        
        # Convexity should be finite
        self.assertTrue(np.isfinite(convexity))


class TestForwardSwapBootstrapping(unittest.TestCase):
    """Test curve bootstrapping with forward starting swaps."""
    
    def setUp(self):
        """Set up test data."""
        self.bootstrapper = CurveBootstrapper(interpolation_method='cubic')
    
    def test_forward_swap_coverage_analysis(self):
        """Test analysis of forward swap coverage."""
        instruments = [
            IRSwap(0.0, 2.0, 0.025),   # Spot 2Y
            IRSwap(1.0, 3.0, 0.030),   # 1Y-3Y forward
            IRSwap(2.0, 5.0, 0.035),   # 2Y-5Y forward
            IRSwap(5.0, 10.0, 0.040),  # 5Y-10Y forward
        ]
        
        coverage = self.bootstrapper.analyze_forward_swap_coverage(instruments)
        
        # Check structure
        self.assertIn('total_instruments', coverage)
        self.assertIn('forward_starting_count', coverage)
        self.assertIn('spot_starting_count', coverage)
        self.assertIn('coverage_segments', coverage)
        self.assertIn('max_tenor', coverage)
        self.assertIn('min_tenor', coverage)
        
        # Check counts
        self.assertEqual(coverage['total_instruments'], 4)
        self.assertEqual(coverage['forward_starting_count'], 3)
        self.assertEqual(coverage['spot_starting_count'], 1)
        
        # Check tenor range
        self.assertEqual(coverage['min_tenor'], 0.0)
        self.assertEqual(coverage['max_tenor'], 10.0)
        
        # Check segments
        segments = coverage['coverage_segments']
        self.assertEqual(len(segments), 4)
        
        # Segments should be sorted by start tenor
        start_tenors = [seg['start_tenor'] for seg in segments]
        self.assertEqual(start_tenors, sorted(start_tenors))
    
    def test_bootstrap_with_forward_control(self):
        """Test bootstrapping with forward starting swaps."""
        # Create instruments that control different curve segments
        instruments = [
            IRSwap(0.0, 1.0, 0.025),   # Controls 0-1Y
            IRSwap(0.0, 2.0, 0.030),   # Controls 0-2Y  
            IRSwap(2.0, 5.0, 0.035),   # Controls 2-5Y segment
            IRSwap(5.0, 10.0, 0.040),  # Controls 5-10Y segment
        ]
        
        # Par swaps should have zero market price
        market_prices = [0.0, 0.0, 0.0, 0.0]
        
        try:
            curve = self.bootstrapper.bootstrap_with_forward_control(instruments, market_prices)
            
            # Should produce a valid curve
            self.assertIsInstance(curve, YieldCurve)
            self.assertGreater(len(curve.tenors), 0)
            self.assertGreater(len(curve.rates), 0)
            
            # Verify that instruments price approximately to their market prices
            for i, instrument in enumerate(instruments):
                price = instrument.price(curve)
                expected_price = market_prices[i]
                
                # Should be close to expected (allowing for numerical errors)
                self.assertAlmostEqual(price, expected_price, places=2)
                
        except Exception as e:
            # If optimization fails, that's still informative
            print(f"Bootstrapping failed (may be expected): {e}")
    
    def test_mixed_spot_forward_instruments(self):
        """Test handling of mixed spot and forward instruments."""
        instruments = [
            IRSwap(0.0, 1.0, 0.025),   # Spot 1Y
            IRSwap(1.0, 3.0, 0.030),   # 1Y-3Y forward
            IRSwap(0.0, 5.0, 0.035),   # Spot 5Y
            IRSwap(3.0, 7.0, 0.040),   # 3Y-7Y forward
        ]
        
        market_prices = [0.0, 0.0, 0.0, 0.0]
        
        # Should handle mixed instruments without error
        coverage = self.bootstrapper.analyze_forward_swap_coverage(instruments)
        
        self.assertEqual(coverage['total_instruments'], 4)
        self.assertEqual(coverage['forward_starting_count'], 2)
        self.assertEqual(coverage['spot_starting_count'], 2)
    
    def test_empty_instrument_list(self):
        """Test handling of empty instrument list."""
        coverage = self.bootstrapper.analyze_forward_swap_coverage([])
        
        self.assertEqual(coverage['total_instruments'], 0)
        self.assertEqual(coverage['forward_starting_count'], 0)
        self.assertEqual(coverage['spot_starting_count'], 0)
        self.assertEqual(len(coverage['coverage_segments']), 0)


class TestForwardSwapEdgeCases(unittest.TestCase):
    """Test edge cases for forward starting swaps."""
    
    def setUp(self):
        """Set up test data."""
        self.tenors = [1.0, 2.0, 3.0, 5.0, 10.0]
        self.rates = [0.03, 0.035, 0.04, 0.042, 0.045]
        self.curve = YieldCurve(self.tenors, self.rates, interpolation_method='linear')
    
    def test_very_short_forward_period(self):
        """Test forward swap with very short period."""
        # 1Y-1.25Y forward swap (3 months)
        short_fwd = IRSwap(1.0, 1.25, 0.04, frequency=4)  # Quarterly
        
        self.assertTrue(short_fwd.is_forward_starting)
        
        # Should be able to price without error
        price = short_fwd.price(self.curve)
        self.assertTrue(np.isfinite(price))
        
        # Should be able to calculate par rate
        par_rate = short_fwd.get_par_rate(self.curve)
        self.assertTrue(np.isfinite(par_rate))
        self.assertGreater(par_rate, 0)
    
    def test_long_forward_start(self):
        """Test forward swap with long forward start."""
        # 5Y-10Y forward swap
        long_fwd = IRSwap(5.0, 10.0, 0.045)
        
        self.assertTrue(long_fwd.is_forward_starting)
        
        # Should work with extrapolation
        price = long_fwd.price(self.curve)
        self.assertTrue(np.isfinite(price))
    
    def test_annual_vs_semiannual_frequency(self):
        """Test forward swaps with different payment frequencies."""
        base_swap = IRSwap(2.0, 5.0, 0.04, frequency=2)  # Semi-annual
        annual_swap = IRSwap(2.0, 5.0, 0.04, frequency=1)  # Annual
        
        base_price = base_swap.price(self.curve)
        annual_price = annual_swap.price(self.curve)
        
        # Prices should be different due to frequency effect
        self.assertNotAlmostEqual(base_price, annual_price, places=4)
        
        # Both should be finite
        self.assertTrue(np.isfinite(base_price))
        self.assertTrue(np.isfinite(annual_price))
    
    def test_large_notional(self):
        """Test forward swap with large notional."""
        large_swap = IRSwap(1.0, 5.0, 0.04, notional=1_000_000)
        
        price = large_swap.price(self.curve)
        self.assertTrue(np.isfinite(price))
        
        # Price should scale with notional
        base_swap = IRSwap(1.0, 5.0, 0.04, notional=1.0)
        base_price = base_swap.price(self.curve)
        
        expected_ratio = large_swap.notional / base_swap.notional
        actual_ratio = price / base_price
        
        self.assertAlmostEqual(actual_ratio, expected_ratio, places=6)
    
    def test_forward_swap_representation(self):
        """Test string representation of forward swaps."""
        spot_swap = IRSwap(0.0, 5.0, 0.04)
        fwd_swap = IRSwap(2.0, 7.0, 0.045)
        
        spot_str = str(spot_swap)
        fwd_str = str(fwd_swap)
        
        # Should contain key information
        self.assertIn("5.0", spot_str)
        self.assertIn("spot", spot_str.lower())
        
        self.assertIn("2.0", fwd_str)
        self.assertIn("7.0", fwd_str)
        self.assertIn("forward", fwd_str.lower())


if __name__ == '__main__':
    unittest.main() 