"""
Yield Curve implementation for interest rate modeling.
"""

import numpy as np
from scipy.interpolate import interp1d
from typing import List, Tuple, Optional, Union
import pandas as pd


class YieldCurve:
    """
    Zero-coupon yield curve with interpolation and forward rate calculations.
    """
    
    def __init__(self, 
                 tenors: List[float], 
                 rates: List[float],
                 interpolation_method: str = 'cubic'):
        """
        Initialize yield curve.
        
        Args:
            tenors: List of tenors in years
            rates: List of zero-coupon rates (annualized)
            interpolation_method: 'linear', 'cubic', or 'log_linear'
        """
        self.tenors = np.array(tenors)
        self.rates = np.array(rates)
        self.interpolation_method = interpolation_method
        
        # Validate inputs
        if len(tenors) != len(rates):
            raise ValueError("Tenors and rates must have same length")
        if not np.all(np.diff(tenors) > 0):
            raise ValueError("Tenors must be strictly increasing")
            
        # Create interpolator
        self._create_interpolator()
    
    def _create_interpolator(self):
        """Create the rate interpolator based on method."""
        if self.interpolation_method == 'linear':
            self._interpolator = interp1d(self.tenors, self.rates, 
                                         kind='linear', fill_value='extrapolate')
        elif self.interpolation_method == 'cubic':
            # Use linear interpolation if we have fewer than 4 points for cubic
            if len(self.tenors) < 4:
                self._interpolator = interp1d(self.tenors, self.rates, 
                                             kind='linear', fill_value='extrapolate')
            else:
                self._interpolator = interp1d(self.tenors, self.rates, 
                                             kind='cubic', fill_value='extrapolate')
        elif self.interpolation_method == 'log_linear':
            # Log-linear interpolation on discount factors
            discount_factors = np.exp(-self.tenors * self.rates)
            self._discount_interpolator = interp1d(self.tenors, discount_factors,
                                                  kind='linear', fill_value='extrapolate')
        else:
            raise ValueError(f"Unknown interpolation method: {self.interpolation_method}")
    
    def get_rate(self, tenor: float) -> float:
        """
        Get interpolated rate at given tenor.
        
        Args:
            tenor: Tenor in years
            
        Returns:
            Interpolated zero-coupon rate
        """
        if self.interpolation_method == 'log_linear':
            # Convert back from discount factor to rate
            df = self._discount_interpolator(tenor)
            return -np.log(df) / tenor
        else:
            return float(self._interpolator(tenor))
    
    def get_discount_factor(self, tenor: float) -> float:
        """
        Get discount factor at given tenor.
        
        Args:
            tenor: Tenor in years
            
        Returns:
            Discount factor
        """
        rate = self.get_rate(tenor)
        return np.exp(-rate * tenor)
    
    def get_forward_rate(self, start_tenor: float, end_tenor: float) -> float:
        """
        Calculate forward rate between two tenors.
        
        Args:
            start_tenor: Start tenor in years
            end_tenor: End tenor in years
            
        Returns:
            Forward rate (annualized)
        """
        if start_tenor >= end_tenor:
            raise ValueError("Start tenor must be less than end tenor")
            
        df_start = self.get_discount_factor(start_tenor)
        df_end = self.get_discount_factor(end_tenor)
        
        # Forward rate calculation
        forward_rate = (np.log(df_start / df_end) / (end_tenor - start_tenor))
        return forward_rate
    
    def get_par_rate(self, tenor: float, frequency: int = 2) -> float:
        """
        Calculate par rate for given tenor and frequency.
        
        Args:
            tenor: Tenor in years
            frequency: Coupon frequency (1=annual, 2=semi-annual, etc.)
            
        Returns:
            Par rate (annualized)
        """
        if tenor <= 0:
            raise ValueError("Tenor must be positive")
            
        # Calculate coupon periods
        periods = int(tenor * frequency)
        period_size = 1.0 / frequency
        
        # Calculate present value of coupons
        coupon_pv = 0.0
        for i in range(1, periods + 1):
            period_tenor = i * period_size
            coupon_pv += self.get_discount_factor(period_tenor)
        
        # Add final principal payment
        principal_pv = self.get_discount_factor(tenor)
        
        # Solve for par rate: 1 = par_rate * coupon_pv + principal_pv
        par_rate = (1.0 - principal_pv) / coupon_pv
        
        return par_rate * frequency  # Convert to annual rate
    
    def shift_curve(self, shift: float) -> 'YieldCurve':
        """
        Create a new curve with parallel shift.
        
        Args:
            shift: Rate shift in basis points (e.g., 10 for 10bp)
            
        Returns:
            New YieldCurve with shifted rates
        """
        shifted_rates = self.rates + shift / 10000.0  # Convert bps to decimal
        return YieldCurve(self.tenors, shifted_rates, self.interpolation_method)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert curve to pandas DataFrame."""
        return pd.DataFrame({
            'tenor': self.tenors,
            'rate': self.rates,
            'discount_factor': [self.get_discount_factor(t) for t in self.tenors]
        })
    
    @classmethod
    def from_instruments(cls, instruments: List, market_prices: List[float],
                        tenors: Optional[List[float]] = None) -> 'YieldCurve':
        """
        Build curve from market instruments using bootstrapping.
        
        Args:
            instruments: List of financial instruments
            market_prices: List of market prices for instruments
            tenors: Optional list of target tenors for curve
            
        Returns:
            Bootstrapped YieldCurve
        """
        from .bootstrapping import CurveBootstrapper
        bootstrapper = CurveBootstrapper()
        return bootstrapper.bootstrap_curve(instruments, market_prices, tenors)
    
    def __repr__(self):
        return f"YieldCurve(tenors={self.tenors}, rates={self.rates}, method='{self.interpolation_method}')" 