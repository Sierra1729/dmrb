"""Unit system configuration using pint.

Enforces physical dimension consistency across the dMRV platform.
No bare floats should cross engine boundaries without units.
"""
from __future__ import annotations

from typing import Any, Union

import pint

# Initialize global unit registry
ureg = pint.UnitRegistry()

# Define carbon accounting domain units
ureg.define("dry_matter = [mass] = dm")
ureg.define("t_dm = 1000 * kilogram * dm = t_dm")
ureg.define("carbon = [mass] = C")
ureg.define("t_C = 1000 * kilogram * C = t_C")
ureg.define("CO2e = [mass] = CO2e")
ureg.define("t_CO2e = 1000 * kilogram * CO2e = t_CO2e")

Q_ = ureg.Quantity
Quantity = pint.Quantity

def to_qty(val: Union[float, int, Quantity], unit_str: str | None = None) -> Quantity:
    """Safely cast value to a pint Quantity with expected unit."""
    if isinstance(val, ureg.Quantity):
        if unit_str:
            return val.to(unit_str)
        return val
    if unit_str is None:
        raise ValueError(f"Unit string required when wrapping bare numeric value {val}")
    return ureg.Quantity(val, unit_str)

def strip_unit(val: Any) -> float:
    """Extract numeric magnitude safely."""
    if isinstance(val, ureg.Quantity):
        return float(val.magnitude)
    return float(val)

__all__ = ["ureg", "Q_", "Quantity", "to_qty", "strip_unit"]
