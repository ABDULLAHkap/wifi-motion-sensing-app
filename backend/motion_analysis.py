"""Lightweight live motion scoring for recent Wi-Fi RSSI samples.

This baseline detector deliberately uses only the Python standard library so the
FastAPI service can run before an ML model is available. It is intended for
calibration and data collection, not precise occupancy counting.
"""

from __future__ import annotations

from math import sqrt
from statistics import fmean
from typing import Any


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def analyze_motion(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Return signal features plus a normalized motion score/state.

    The heuristic emphasizes short-term RSSI variability and consecutive RSSI
    changes. The thresholds are conservative starting values and should later be
    replaced/tuned using real recordings from each room/router/phone setup.
    """
    rssi = [float(sample["rssi"]) for sample in samples if sample.get("rssi") is not None]

    if len(rssi) < 5:
        return {
            "ready": False,
            "sample_count": len(rssi),
            "minimum_samples": 5,
            "motion_score": 0.0,
            "motion_state": "CALIBRATING",
            "features": {},
        }

    mean = fmean(rssi)
    variance = fmean([(value - mean) ** 2 for value in rssi])
    std = sqrt(variance)
    rssi_range = max(rssi) - min(rssi)

    changes = [abs(current - previous) for previous, current in zip(rssi, rssi[1:])]
    change_mean = fmean(changes) if changes else 0.0
    change_max = max(changes, default=0.0)
    peak_count = sum(1 for change in changes if change >= max(2.0, std * 1.5))

    # Normalize several indicators into a robust first-pass 0..1 score.
    variability_score = _clamp(std / 4.0)
    range_score = _clamp(rssi_range / 12.0)
    change_score = _clamp(change_mean / 3.0)
    peak_score = _clamp(peak_count / max(2.0, len(changes) * 0.25))

    motion_score = _clamp(
        0.40 * variability_score
        + 0.25 * change_score
        + 0.20 * range_score
        + 0.15 * peak_score
    )

    if motion_score >= 0.62:
        state = "MOTION"
    elif motion_score >= 0.38:
        state = "POSSIBLE_MOTION"
    else:
        state = "NO_MOTION"

    return {
        "ready": True,
        "sample_count": len(rssi),
        "motion_score": round(motion_score, 4),
        "motion_state": state,
        "features": {
            "rssi_mean": round(mean, 3),
            "rssi_std": round(std, 3),
            "rssi_variance": round(variance, 3),
            "rssi_range": round(rssi_range, 3),
            "rssi_change_mean": round(change_mean, 3),
            "rssi_change_max": round(change_max, 3),
            "peak_count": peak_count,
        },
    }
