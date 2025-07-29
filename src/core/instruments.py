"""
Financial instruments for interest rate modeling.
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .curve import YieldCurve


class Instrument(ABC):
    """Abstract base class for financial instruments."""
    
    def __init__(self, notional: float = 1.0):
        self.notional = notional
    
    @abstractmethod
    def price(self, curve: YieldCurve) -> float:
        """Price the instrument using the given yield curve."""
        pass
    
    @abstractmethod
    def get_cashflows(self, curve: YieldCurve) -> Dict[str, List[float]]:
        """Get cashflow dates and amounts."""
        pass
    
    def get_dv01(self, curve: YieldCurve, shift: float = 1.0) -> float:
        """
        Calculate DV01 (dollar value of 1bp change).
        
        Args:
            curve: Yield curve
            shift: Rate shift in basis points
            
        Returns:
            DV01
        """
        base_price = self.price(curve)
        shifted_curve = curve.shift_curve(shift)
        shifted_price = self.price(shifted_curve)
        
        return (base_price - shifted_price) / (shift / 10000.0)
    
    def get_convexity(self, curve: YieldCurve, shift: float = 10.0) -> float:
        """
        Calculate convexity.
        
        Args:
            curve: Yield curve
            shift: Rate shift in basis points
            
        Returns:
            Convexity
        """
        base_price = self.price(curve)
        up_curve = curve.shift_curve(shift)
        down_curve = curve.shift_curve(-shift)
        
        up_price = self.price(up_curve)
        down_price = self.price(down_curve)
        
        shift_decimal = shift / 10000.0
        convexity = (up_price + down_price - 2 * base_price) / (shift_decimal ** 2)
        
        return convexity


class IRSwap(Instrument):
    """
    Interest Rate Swap instrument.
    Supports both spot-starting and forward-starting swaps.
    """
    
    def __init__(self, 
                 start_date: float,
                 maturity: float,
                 fixed_rate: float,
                 frequency: int = 2,
                 notional: float = 1.0,
                 day_count: str = '30/360'):
        """
        Initialize interest rate swap.
        
        Args:
            start_date: Start date in years from today (0.0 = spot start, >0 = forward start)
            maturity: Maturity in years from today
            fixed_rate: Fixed rate (annualized)
            frequency: Coupon frequency (1=annual, 2=semi-annual, etc.)
            notional: Notional amount
            day_count: Day count convention
        """
        super().__init__(notional)
        self.start_date = start_date
        self.maturity = maturity
        self.fixed_rate = fixed_rate
        self.frequency = frequency
        self.day_count = day_count
        
        if self.start_date >= self.maturity:
            raise ValueError("Start date must be before maturity")
        
        # Calculate payment dates
        self._calculate_payment_dates()
    
    def _calculate_payment_dates(self):
        """Calculate payment dates for the swap."""
        period_size = 1.0 / self.frequency
        self.payment_dates = []
        
        # Start from first payment date after start_date
        current_date = self.start_date + period_size
        while current_date <= self.maturity:
            self.payment_dates.append(current_date)
            current_date += period_size
        
        # Ensure maturity is included
        if len(self.payment_dates) == 0 or abs(self.payment_dates[-1] - self.maturity) > 1e-6:
            self.payment_dates.append(self.maturity)
    
    @property
    def effective_tenor(self) -> float:
        """Get the tenor that this swap controls in curve building (maturity for spot, start->maturity for forward)."""
        return self.maturity
    
    @property 
    def forward_tenor_range(self) -> tuple:
        """Get the tenor range this forward swap controls."""
        return (self.start_date, self.maturity)
    
    @property
    def is_forward_starting(self) -> bool:
        """Check if this is a forward starting swap."""
        return self.start_date > 1e-6  # Tolerance for floating point
    
    def price(self, curve: YieldCurve) -> float:
        """
        Price the swap using the yield curve.
        
        For forward starting swaps, this calculates the present value of the entire swap
        including the forward period.
        
        Args:
            curve: Yield curve
            
        Returns:
            Present value of the swap
        """
        # Calculate fixed leg value
        fixed_leg = self._price_fixed_leg(curve)
        
        # Calculate floating leg value
        floating_leg = self._price_floating_leg(curve)
        
        # Swap value = Floating leg - Fixed leg (receiver perspective)
        return floating_leg - fixed_leg
    
    def _price_fixed_leg(self, curve: YieldCurve) -> float:
        """Price the fixed leg of the swap."""
        fixed_leg_pv = 0.0
        
        for payment_date in self.payment_dates:
            # Calculate coupon amount
            coupon = self.fixed_rate / self.frequency * self.notional
            
            # Discount to present value
            discount_factor = curve.get_discount_factor(payment_date)
            fixed_leg_pv += coupon * discount_factor
        
        return fixed_leg_pv
    
    def _price_floating_leg(self, curve: YieldCurve) -> float:
        """
        Price the floating leg of the swap.
        
        For forward starting swaps, the floating leg value is calculated as:
        Notional * (DF(start) - DF(maturity))
        
        This represents the present value of receiving floating payments.
        """
        # Get discount factors
        start_df = curve.get_discount_factor(self.start_date)
        maturity_df = curve.get_discount_factor(self.maturity)
        
        # Floating leg PV = Notional * (DF_start - DF_maturity)
        floating_leg_pv = self.notional * (start_df - maturity_df)
        
        return floating_leg_pv
    
    def get_par_rate(self, curve: YieldCurve) -> float:
        """
        Calculate the par rate (fair fixed rate) for this swap given the curve.
        This is the fixed rate that makes the swap value zero.
        
        Returns:
            Par swap rate
        """
        # Calculate floating leg value
        floating_leg_pv = self._price_floating_leg(curve)
        
        # Calculate annuity (present value of 1 unit per period)
        annuity = 0.0
        for payment_date in self.payment_dates:
            discount_factor = curve.get_discount_factor(payment_date)
            annuity += discount_factor / self.frequency
        
        # Par rate = Floating leg PV / Annuity
        if annuity == 0:
            raise ValueError("Annuity is zero - cannot calculate par rate")
        
        return floating_leg_pv / (annuity * self.notional)
    
    def get_forward_rate_sensitivity(self, curve: YieldCurve, start_tenor: float, end_tenor: float) -> float:
        """
        Calculate sensitivity to a specific forward rate segment.
        Useful for understanding which part of the curve this swap is most sensitive to.
        
        Args:
            curve: Yield curve
            start_tenor: Start of the rate segment
            end_tenor: End of the rate segment
            
        Returns:
            Sensitivity (price change per 1bp rate change in that segment)
        """
        # This is a simplified calculation - in practice you'd use more sophisticated methods
        if self.start_date <= start_tenor and end_tenor <= self.maturity:
            # This forward rate segment affects our swap
            period_length = end_tenor - start_tenor
            avg_df = (curve.get_discount_factor(start_tenor) + curve.get_discount_factor(end_tenor)) / 2
            return self.notional * period_length * avg_df * 0.0001  # Per 1bp
        return 0.0
    
    def get_cashflows(self, curve: YieldCurve) -> Dict[str, List[float]]:
        """Get cashflow dates and amounts."""
        fixed_cashflows = []
        floating_cashflows = []
        
        # Fixed leg cashflows
        for payment_date in self.payment_dates:
            fixed_coupon = self.fixed_rate / self.frequency * self.notional
            fixed_cashflows.append(fixed_coupon)
        
        # Floating leg cashflows (forward rates for each period)
        prev_date = self.start_date
        for payment_date in self.payment_dates:
            if prev_date < payment_date:
                forward_rate = curve.get_forward_rate(prev_date, payment_date)
                floating_coupon = forward_rate / self.frequency * self.notional
                floating_cashflows.append(floating_coupon)
            prev_date = payment_date
        
        return {
            'dates': self.payment_dates,
            'fixed': fixed_cashflows,
            'floating': floating_cashflows
        }
    
    def __repr__(self):
        if self.is_forward_starting:
            return f"IRSwap(forward: {self.start_date}Y-{self.maturity}Y, rate={self.fixed_rate:.4f})"
        else:
            return f"IRSwap(spot: {self.maturity}Y, rate={self.fixed_rate:.4f})"


class IRFuture(Instrument):
    """
    Interest Rate Future instrument (e.g., Eurodollar futures).
    """
    
    def __init__(self, 
                 start_date: float,
                 maturity: float,
                 notional: float = 1.0,
                 contract_size: float = 1.0):
        """
        Initialize interest rate future.
        
        Args:
            start_date: Start date in years from today
            maturity: Maturity in years from today
            notional: Notional amount
            contract_size: Contract size multiplier
        """
        super().__init__(notional)
        self.start_date = start_date
        self.maturity = maturity
        self.contract_size = contract_size
    
    def price(self, curve: YieldCurve) -> float:
        """
        Price the future using the yield curve.
        
        Args:
            curve: Yield curve
            
        Returns:
            Future price
        """
        # Get forward rate for the period
        forward_rate = curve.get_forward_rate(self.start_date, self.maturity)
        
        # Future price = 100 - forward_rate (in percentage)
        future_price = 100.0 - forward_rate * 100.0
        
        return future_price * self.contract_size * self.notional
    
    def get_cashflows(self, curve: YieldCurve) -> Dict[str, List[float]]:
        """Get cashflow dates and amounts."""
        # Futures are marked-to-market daily, but for simplicity
        # we'll just return the final settlement
        forward_rate = curve.get_forward_rate(self.start_date, self.maturity)
        settlement_amount = (100.0 - forward_rate * 100.0) * self.contract_size * self.notional
        
        return {
            'dates': [self.maturity],
            'settlement': [settlement_amount]
        }
    
    def get_implied_rate(self, market_price: float) -> float:
        """
        Get implied forward rate from market price.
        
        Args:
            market_price: Market price of the future
            
        Returns:
            Implied forward rate
        """
        # Future price = 100 - rate, so rate = 100 - price
        implied_rate = (100.0 - market_price) / 100.0
        return implied_rate
    
    def __repr__(self):
        return f"IRFuture(start={self.start_date}, maturity={self.maturity})" 