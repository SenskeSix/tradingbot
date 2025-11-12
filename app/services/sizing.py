from __future__ import annotations


def position_size_fixed_fraction(cash: float, fraction: float, price: float) -> float:
    if price <= 0:
        return 0
    return round((cash * fraction) / price, 6)


def position_size_vol_scaled(price: float, atr_proxy: float | None, fallback_fraction: float, cash: float) -> tuple[float, str]:
    if not atr_proxy:
        return position_size_fixed_fraction(cash, fallback_fraction, price), "fallback_fixed_fraction"
    vol_factor = max(atr_proxy / price, 0.01)
    qty = (cash * fallback_fraction * (1 - vol_factor)) / price
    return round(qty, 6), "vol_scaled"
