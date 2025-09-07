from __future__ import annotations

from typing import Dict


def derive_zones(predicted_10k_sec: int) -> Dict[str, dict]:
    """Return pace windows per zone in sec/km and sec/mi.

    Approximate from 10K pace. These are rough, conservative bands.
    """
    if predicted_10k_sec <= 0:
        raise ValueError("predicted_10k_sec must be positive")

    # 10k pace per km and mile
    pace_10k_per_km = predicted_10k_sec / 10.0
    pace_10k_per_mi = predicted_10k_sec / 6.21371

    def window(base: float, plus_low: float, plus_high: float) -> dict:
        return {
            "sec_per_km": [int(base + plus_low), int(base + plus_high)],
            "sec_per_mi": [int(pace_10k_per_mi + plus_low * 1.60934), int(pace_10k_per_mi + plus_high * 1.60934)],
        }

    zones = {
        "easy": window(pace_10k_per_km, 60, 120),
        "aerobic": window(pace_10k_per_km, 30, 60),
        "threshold": {  # around 10K pace +/- ~10-20 s/mi slower
            "sec_per_km": [int(pace_10k_per_km + 0), int(pace_10k_per_km + 20 / 1.60934)],
            "sec_per_mi": [int(pace_10k_per_mi - 10), int(pace_10k_per_mi + 20)],
        },
        "interval": {  # faster than 5K pace approximated as ~ -10-20 s/mi from 10K pace
            "sec_per_km": [int(pace_10k_per_km - 20 / 1.60934), int(pace_10k_per_km - 5 / 1.60934)],
            "sec_per_mi": [int(pace_10k_per_mi - 20), int(pace_10k_per_mi - 5)],
        },
        "long": window(pace_10k_per_km, 45, 105),
    }
    return zones

