from __future__ import annotations

from math import erf, exp, log, pi, sqrt


def norm_cdf(x: float) -> float:
    return 0.5 * (1 + erf(x / sqrt(2)))


def norm_pdf(x: float) -> float:
    return exp(-0.5 * x * x) / sqrt(2 * pi)


def black76_price(F: float, K: float, r: float, sigma: float, T: float, option_type: str = "call") -> float:
    if T <= 0 or sigma <= 0 or F <= 0 or K <= 0:
        raise ValueError("F, K, sigma and T must be positive")
    d1 = (log(F / K) + 0.5 * sigma * sigma * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    df = exp(-r * T)
    if option_type.lower().startswith("c"):
        return df * (F * norm_cdf(d1) - K * norm_cdf(d2))
    return df * (K * norm_cdf(-d2) - F * norm_cdf(-d1))


def black76_greeks(F: float, K: float, r: float, sigma: float, T: float, option_type: str = "call") -> dict:
    d1 = (log(F / K) + 0.5 * sigma * sigma * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    df = exp(-r * T)
    cp = 1 if option_type.lower().startswith("c") else -1
    price = black76_price(F, K, r, sigma, T, option_type)
    delta = cp * df * norm_cdf(cp * d1)
    gamma = df * norm_pdf(d1) / (F * sigma * sqrt(T))
    vega = df * F * norm_pdf(d1) * sqrt(T) / 100  # per 1 vol point
    theta = (-(df * F * norm_pdf(d1) * sigma) / (2 * sqrt(T)) + cp * r * df * (F * norm_cdf(cp*d1) - K * norm_cdf(cp*d2))) / 365
    return {"price": price, "delta": delta, "gamma": gamma, "vega_1pct": vega, "theta_1d": theta, "d1": d1, "d2": d2}
