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
            start_date: Start date in years from today
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
        
        # Calculate payment dates
        self._calculate_payment_dates()
    
    def _calculate_payment_dates(self):
        """Calculate payment dates for the swap."""
        period_size = 1.0 / self.frequency
        self.payment_dates = []
        
        current_date = self.start_date
        while current_date <= self.maturity:
            self.payment_dates.append(current_date)
            current_date += period_size
        
        # Ensure maturity is included
        if self.maturity not in self.payment_dates:
            self.payment_dates.append(self.maturity)
    
    def price(self, curve: YieldCurve) -> float:
        """
        Price the swap using the yield curve.
        
        Args:
            curve: Yield curve
            
        Returns:
            Present value of the swap
        """
        # Calculate fixed leg value
        fixed_leg = self._price_fixed_leg(curve)
        
        # Calculate floating leg value
        floating_leg = self._price_floating_leg(curve)
        
        # Swap value = Floating leg - Fixed leg
        return floating_leg - fixed_leg
    
    def _price_fixed_leg(self, curve: YieldCurve) -> float:
        """Price the fixed leg of the swap."""
        fixed_leg_pv = 0.0
        
        for i, payment_date in enumerate(self.payment_dates):
            if i == 0:  # Skip first payment date (no coupon)
                continue
                
            # Calculate coupon amount
            coupon = self.fixed_rate / self.frequency * self.notional
            
            # Discount to present value
            discount_factor = curve.get_discount_factor(payment_date)
            fixed_leg_pv += coupon * discount_factor
        
        # Add final principal payment
        final_discount = curve.get_discount_factor(self.maturity)
        fixed_leg_pv += self.notional * final_discount
        
        return fixed_leg_pv
    
    def _price_floating_leg(self, curve: YieldCurve) -> float:
        """Price the floating leg of the swap."""
        # For a par swap, floating leg = notional at start
        # This is a simplified approach - in practice, you'd need to handle
        # the floating rate reset mechanism more carefully
        
        # Calculate forward rates for each period
        floating_leg_pv = 0.0
        
        for i in range(len(self.payment_dates) - 1):
            start_date = self.payment_dates[i]
            end_date = self.payment_dates[i + 1]
            
            # Get forward rate for this period
            forward_rate = curve.get_forward_rate(start_date, end_date)
            
            # Calculate floating payment
            floating_payment = forward_rate / self.frequency * self.notional
            
            # Discount to present value
            discount_factor = curve.get_discount_factor(end_date)
            floating_leg_pv += floating_payment * discount_factor
        
        # Add final principal payment
        final_discount = curve.get_discount_factor(self.maturity)
        floating_leg_pv += self.notional * final_discount
        
        return floating_leg_pv
    
    def get_cashflows(self, curve: YieldCurve) -> Dict[str, List[float]]:
        """Get cashflow dates and amounts."""
        fixed_cashflows = []
        floating_cashflows = []
        
        for i, payment_date in enumerate(self.payment_dates):
            if i == 0:  # Skip first payment date
                continue
                
            # Fixed cashflow
            fixed_coupon = self.fixed_rate / self.frequency * self.notional
            fixed_cashflows.append(fixed_coupon)
            
            # Floating cashflow (simplified)
            if i < len(self.payment_dates) - 1:
                start_date = self.payment_dates[i - 1]
                end_date = payment_date
                forward_rate = curve.get_forward_rate(start_date, end_date)
                floating_coupon = forward_rate / self.frequency * self.notional
                floating_cashflows.append(floating_coupon)
            else:
                floating_cashflows.append(0.0)  # Final principal payment handled separately
        
        return {
            'dates': self.payment_dates[1:],  # Skip first date
            'fixed': fixed_cashflows,
            'floating': floating_cashflows
        }
    
    def __repr__(self):
        return f"IRSwap(start={self.start_date}, maturity={self.maturity}, rate={self.fixed_rate})"


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