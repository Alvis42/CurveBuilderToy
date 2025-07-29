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
                 interpolation_method: str = 'cubic',
                 cutoff_tenor: Optional[float] = None,
                 pre_cutoff_method: str = 'flat',
                 post_cutoff_method: str = 'cubic'):
        """
        Initialize yield curve.
        
        Args:
            tenors: List of tenors in years
            rates: List of zero-coupon rates (annualized)
            interpolation_method: 'linear', 'cubic', 'log_linear', 'flat', or 'hybrid'
            cutoff_tenor: Tenor threshold for hybrid interpolation (only used if method='hybrid')
            pre_cutoff_method: Interpolation method before cutoff (default: 'flat')
            post_cutoff_method: Interpolation method after cutoff (default: 'cubic')
        """
        self.tenors = np.array(tenors)
        self.rates = np.array(rates)
        self.interpolation_method = interpolation_method
        self.cutoff_tenor = cutoff_tenor
        self.pre_cutoff_method = pre_cutoff_method
        self.post_cutoff_method = post_cutoff_method
        
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
        elif self.interpolation_method == 'flat':
            # Flat (step function) interpolation - suitable for SOFR/Fed Fund rates
            # Rate stays constant between nodes (left-continuous step function)
            self._interpolator = interp1d(self.tenors, self.rates, 
                                         kind='previous', fill_value='extrapolate')
        elif self.interpolation_method == 'hybrid':
            # Hybrid interpolation using two different methods before and after cutoff
            if self.cutoff_tenor is None:
                raise ValueError("cutoff_tenor must be specified for hybrid interpolation")
            
            # Split data at cutoff point
            self._create_hybrid_interpolators()
        else:
            raise ValueError(f"Unknown interpolation method: {self.interpolation_method}")
    
    def _create_hybrid_interpolators(self):
        """Create separate interpolators for pre and post cutoff periods."""
        # Find the cutoff index
        cutoff_idx = np.searchsorted(self.tenors, self.cutoff_tenor, side='right')
        
        # Ensure we have at least one point on each side
        if cutoff_idx == 0:
            # All points are after cutoff, use post-cutoff method for all
            self._pre_tenors = np.array([])
            self._pre_rates = np.array([])
            self._post_tenors = self.tenors
            self._post_rates = self.rates
        elif cutoff_idx >= len(self.tenors):
            # All points are before cutoff, use pre-cutoff method for all
            self._pre_tenors = self.tenors
            self._pre_rates = self.rates
            self._post_tenors = np.array([])
            self._post_rates = np.array([])
        else:
            # Add the cutoff point by interpolating if it doesn't exist
            if not np.any(np.isclose(self.tenors, self.cutoff_tenor)):
                # Interpolate rate at cutoff using linear interpolation
                temp_interpolator = interp1d(self.tenors, self.rates, 
                                           kind='linear', fill_value='extrapolate')
                cutoff_rate = temp_interpolator(self.cutoff_tenor)
                
                # Split the data including the cutoff point
                self._pre_tenors = np.concatenate([self.tenors[:cutoff_idx], [self.cutoff_tenor]])
                self._pre_rates = np.concatenate([self.rates[:cutoff_idx], [cutoff_rate]])
                self._post_tenors = np.concatenate([[self.cutoff_tenor], self.tenors[cutoff_idx:]])
                self._post_rates = np.concatenate([[cutoff_rate], self.rates[cutoff_idx:]])
            else:
                # Cutoff point exists in data
                exact_idx = np.where(np.isclose(self.tenors, self.cutoff_tenor))[0][0]
                self._pre_tenors = self.tenors[:exact_idx+1]
                self._pre_rates = self.rates[:exact_idx+1]
                self._post_tenors = self.tenors[exact_idx:]
                self._post_rates = self.rates[exact_idx:]
        
        # Create pre-cutoff interpolator
        if len(self._pre_tenors) > 0:
            self._pre_interpolator = self._create_single_interpolator(
                self._pre_tenors, self._pre_rates, self.pre_cutoff_method
            )
        else:
            self._pre_interpolator = None
            
        # Create post-cutoff interpolator
        if len(self._post_tenors) > 0:
            self._post_interpolator = self._create_single_interpolator(
                self._post_tenors, self._post_rates, self.post_cutoff_method
            )
        else:
            self._post_interpolator = None
    
    def _create_single_interpolator(self, tenors, rates, method):
        """Create a single interpolator for given method."""
        if method == 'linear':
            return interp1d(tenors, rates, kind='linear', fill_value='extrapolate')
        elif method == 'cubic':
            if len(tenors) < 4:
                return interp1d(tenors, rates, kind='linear', fill_value='extrapolate')
            else:
                return interp1d(tenors, rates, kind='cubic', fill_value='extrapolate')
        elif method == 'flat':
            return interp1d(tenors, rates, kind='previous', fill_value='extrapolate')
        elif method == 'log_linear':
            discount_factors = np.exp(-tenors * rates)
            return interp1d(tenors, discount_factors, kind='linear', fill_value='extrapolate')
        else:
            raise ValueError(f"Unknown interpolation method: {method}")
    
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
        elif self.interpolation_method == 'flat':
            # For flat interpolation, we need custom logic for extrapolation
            if tenor <= self.tenors[0]:
                return float(self.rates[0])
            elif tenor >= self.tenors[-1]:
                return float(self.rates[-1])
            else:
                # Find the index where tenor fits
                idx = np.searchsorted(self.tenors, tenor, side='right') - 1
                return float(self.rates[idx])
        elif self.interpolation_method == 'hybrid':
            # Use appropriate interpolator based on cutoff
            if tenor <= self.cutoff_tenor:
                if self._pre_interpolator is None:
                    # No pre-cutoff data, use post-cutoff method
                    return self._get_rate_from_interpolator(tenor, self._post_interpolator, self.post_cutoff_method)
                return self._get_rate_from_interpolator(tenor, self._pre_interpolator, self.pre_cutoff_method)
            else:
                if self._post_interpolator is None:
                    # No post-cutoff data, use pre-cutoff method
                    return self._get_rate_from_interpolator(tenor, self._pre_interpolator, self.pre_cutoff_method)
                return self._get_rate_from_interpolator(tenor, self._post_interpolator, self.post_cutoff_method)
        else:
            return float(self._interpolator(tenor))
    
    def _get_rate_from_interpolator(self, tenor: float, interpolator, method: str) -> float:
        """Get rate from a specific interpolator with method-specific logic."""
        if method == 'flat':
            # Custom flat interpolation logic
            if interpolator == self._pre_interpolator:
                tenors, rates = self._pre_tenors, self._pre_rates
            else:
                tenors, rates = self._post_tenors, self._post_rates
                
            if tenor <= tenors[0]:
                return float(rates[0])
            elif tenor >= tenors[-1]:
                return float(rates[-1])
            else:
                idx = np.searchsorted(tenors, tenor, side='right') - 1
                return float(rates[idx])
        elif method == 'log_linear':
            # Convert back from discount factor to rate
            df = interpolator(tenor)
            return -np.log(df) / tenor
        else:
            return float(interpolator(tenor))
    
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