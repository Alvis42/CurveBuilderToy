"""
Curve bootstrapping algorithms for building yield curves from market instruments.
"""

import numpy as np
from scipy.optimize import minimize
from typing import List, Optional, Tuple
from .curve import YieldCurve
from .instruments import Instrument


class CurveBootstrapper:
    """
    Bootstrapper for building yield curves from market instruments.
    """
    
    def __init__(self, interpolation_method: str = 'cubic'):
        """
        Initialize bootstrapper.
        
        Args:
            interpolation_method: Interpolation method for the curve
        """
        self.interpolation_method = interpolation_method
    
    def bootstrap_curve(self, 
                       instruments: List[Instrument],
                       market_prices: List[float],
                       target_tenors: Optional[List[float]] = None) -> YieldCurve:
        """
        Bootstrap yield curve from market instruments.
        
        Args:
            instruments: List of financial instruments
            market_prices: List of market prices for instruments
            target_tenors: Optional list of target tenors for curve
            
        Returns:
            Bootstrapped YieldCurve
        """
        if len(instruments) != len(market_prices):
            raise ValueError("Instruments and market prices must have same length")
        
        # Extract tenors from instruments
        tenors = self._extract_tenors(instruments)
        
        # If no target tenors specified, use instrument tenors
        if target_tenors is None:
            target_tenors = tenors
        
        # Initialize rates (can be improved with better initial guess)
        initial_rates = self._get_initial_rates(tenors)
        
        # Optimize rates to match market prices
        optimized_rates = self._optimize_rates(
            instruments, market_prices, tenors, initial_rates
        )
        
        # Create yield curve
        curve = YieldCurve(tenors, optimized_rates, self.interpolation_method)
        
        return curve
    
    def _extract_tenors(self, instruments: List[Instrument]) -> List[float]:
        """Extract tenors from instruments."""
        tenors = []
        
        for instrument in instruments:
            if hasattr(instrument, 'maturity'):
                tenors.append(instrument.maturity)
            elif hasattr(instrument, 'start_date') and hasattr(instrument, 'maturity'):
                # For futures, use the period midpoint
                mid_tenor = (instrument.start_date + instrument.maturity) / 2
                tenors.append(mid_tenor)
        
        # Sort and remove duplicates
        tenors = sorted(list(set(tenors)))
        return tenors
    
    def _get_initial_rates(self, tenors: List[float]) -> List[float]:
        """Get initial rate guess for bootstrapping."""
        # Simple linear interpolation from short to long rates
        # In practice, you might use market data or a more sophisticated approach
        
        if len(tenors) == 1:
            return [0.05]  # 5% default
        
        # Create a simple upward sloping curve
        short_rate = 0.02  # 2%
        long_rate = 0.06   # 6%
        
        rates = []
        for tenor in tenors:
            # Linear interpolation between short and long rates
            if tenor <= 1.0:
                rate = short_rate
            elif tenor >= 10.0:
                rate = long_rate
            else:
                # Interpolate between 1Y and 10Y
                rate = short_rate + (long_rate - short_rate) * (tenor - 1.0) / 9.0
            
            rates.append(rate)
        
        return rates
    
    def _optimize_rates(self, 
                       instruments: List[Instrument],
                       market_prices: List[float],
                       tenors: List[float],
                       initial_rates: List[float]) -> List[float]:
        """
        Optimize rates to match market prices.
        
        Args:
            instruments: List of instruments
            market_prices: Market prices
            tenors: Tenors for the curve
            initial_rates: Initial rate guess
            
        Returns:
            Optimized rates
        """
        def objective_function(rates):
            """Objective function to minimize pricing errors."""
            # Create temporary curve
            temp_curve = YieldCurve(tenors, rates, self.interpolation_method)
            
            # Calculate pricing errors
            errors = []
            for instrument, market_price in zip(instruments, market_prices):
                model_price = instrument.price(temp_curve)
                error = (model_price - market_price) / market_price  # Relative error
                errors.append(error)
            
            # Return sum of squared errors
            return np.sum(np.array(errors) ** 2)
        
        # Optimize using scipy
        result = minimize(
            objective_function,
            initial_rates,
            method='L-BFGS-B',
            bounds=[(0.0, 0.20) for _ in tenors],  # Rates between 0% and 20%
            options={'maxiter': 1000}
        )
        
        if not result.success:
            print(f"Warning: Optimization failed to converge: {result.message}")
        
        return result.x.tolist()
    
    def bootstrap_from_swaps(self, 
                            swap_rates: List[float],
                            swap_tenors: List[float],
                            frequency: int = 2) -> YieldCurve:
        """
        Bootstrap curve from swap rates (simplified approach).
        
        Args:
            swap_rates: List of swap rates (annualized)
            swap_tenors: List of swap tenors in years
            frequency: Coupon frequency
            
        Returns:
            Bootstrapped YieldCurve
        """
        if len(swap_rates) != len(swap_tenors):
            raise ValueError("Swap rates and tenors must have same length")
        
        # Sort by tenor
        sorted_data = sorted(zip(swap_tenors, swap_rates))
        tenors, rates = zip(*sorted_data)
        
        # Bootstrap zero-coupon rates from swap rates
        zero_rates = self._bootstrap_zero_rates(list(tenors), list(rates), frequency)
        
        return YieldCurve(list(tenors), zero_rates, self.interpolation_method)
    
    def _bootstrap_zero_rates(self, 
                             tenors: List[float], 
                             swap_rates: List[float],
                             frequency: int) -> List[float]:
        """
        Bootstrap zero-coupon rates from swap rates.
        
        Args:
            tenors: Swap tenors
            swap_rates: Swap rates
            frequency: Coupon frequency
            
        Returns:
            Zero-coupon rates
        """
        zero_rates = []
        
        for i, (tenor, swap_rate) in enumerate(zip(tenors, swap_rates)):
            if i == 0:
                # First rate is the swap rate
                zero_rates.append(swap_rate)
            else:
                # Bootstrap subsequent rates
                zero_rate = self._bootstrap_single_rate(
                    tenor, swap_rate, tenors[:i], zero_rates, frequency
                )
                zero_rates.append(zero_rate)
        
        return zero_rates
    
    def _bootstrap_single_rate(self, 
                              tenor: float,
                              swap_rate: float,
                              known_tenors: List[float],
                              known_rates: List[float],
                              frequency: int) -> float:
        """
        Bootstrap a single zero-coupon rate.
        
        Args:
            tenor: Target tenor
            swap_rate: Swap rate for this tenor
            known_tenors: Known tenors
            known_rates: Known zero-coupon rates
            frequency: Coupon frequency
            
        Returns:
            Zero-coupon rate for the target tenor
        """
        # Create temporary curve with known rates
        temp_curve = YieldCurve(known_tenors, known_rates, self.interpolation_method)
        
        # Calculate periods
        periods = int(tenor * frequency)
        period_size = 1.0 / frequency
        
        # Calculate present value of coupons using known rates
        coupon_pv = 0.0
        for i in range(1, periods):
            period_tenor = i * period_size
            if period_tenor <= known_tenors[-1]:
                discount_factor = temp_curve.get_discount_factor(period_tenor)
                coupon_pv += discount_factor
        
        # Calculate present value of final principal using known rates
        principal_pv = 0.0
        if tenor <= known_tenors[-1]:
            principal_pv = temp_curve.get_discount_factor(tenor)
        
        # Solve for the unknown zero-coupon rate
        # The equation is: 1 = swap_rate * coupon_pv + principal_pv + final_discount_factor
        # where final_discount_factor = exp(-rate * tenor)
        
        coupon_amount = swap_rate / frequency
        remaining_coupons = coupon_amount * (periods - len([t for t in known_tenors if t < tenor]))
        
        # Solve for the zero-coupon rate
        if remaining_coupons > 0:
            # Use Newton-Raphson or similar method
            # For simplicity, we'll use a numerical approach
            def objective(rate):
                final_df = np.exp(-rate * tenor)
                total_pv = coupon_amount * coupon_pv + principal_pv + final_df
                return total_pv - 1.0
            
            # Simple bisection method
            rate_low, rate_high = 0.0, 0.20
            for _ in range(50):
                rate_mid = (rate_low + rate_high) / 2
                if objective(rate_mid) > 0:
                    rate_high = rate_mid
                else:
                    rate_low = rate_mid
            
            return rate_mid
        else:
            # No remaining coupons, just solve for final discount factor
            final_df = (1.0 - coupon_amount * coupon_pv - principal_pv)
            return -np.log(final_df) / tenor 