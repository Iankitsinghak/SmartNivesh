from dataclasses import dataclass

from app.core.constants import RADIUS_BANDS_KM
from app.utils.geo import haversine_km


@dataclass(frozen=True)
class DistanceResult:
    distance_km: float
    band: str
    method: str
    decay: float


def radius_band(distance_km: float) -> str | None:
    for lower, upper in RADIUS_BANDS_KM:
        if lower <= distance_km <= upper:
            return f"{int(lower)}-{int(upper)} km"
    return None


def bounded_distance_decay(distance_km: float, maximum_km: float = 10.0) -> float:
    if distance_km < 0 or maximum_km <= 0:
        raise ValueError("distance and maximum radius must be positive")
    return max(0.0, min(1.0, 1.0 - distance_km / maximum_km))


def straight_line_distance(
    latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float
) -> DistanceResult:
    distance_km = haversine_km(latitude_a, longitude_a, latitude_b, longitude_b)
    band = radius_band(distance_km)
    if band is None:
        raise ValueError("distance is outside the supported 0-10 km catchment")
    return DistanceResult(
        distance_km=round(distance_km, 3),
        band=band,
        method="straight_line_haversine",
        decay=round(bounded_distance_decay(distance_km), 3),
    )