from __future__ import annotations

from dataclasses import dataclass

from ..config import get_settings


DEFAULT_RIEGEL_K = 1.06


@dataclass
class FitnessProjection:
    distance_m: int
    predicted_time_sec: int


def riegel_predict(t1_sec: int, d1_m: int, d2_m: int, k: float | None = None) -> int:
    """Return predicted time (sec) for distance d2 given t1@d1.

    Uses Riegel formula: T2 = T1 * (D2/D1)^k
    """
    if d1_m <= 0 or d2_m <= 0:
        raise ValueError("Distances must be positive")
    k_eff = float(get_settings().riegel_k if k is None else k)
    t2 = float(t1_sec) * (float(d2_m) / float(d1_m)) ** k_eff
    return max(1, int(round(t2)))

