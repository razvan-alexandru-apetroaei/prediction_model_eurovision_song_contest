"""
Geographic proximity between Eurovision countries.
proxy = exp(-distance_km / 1500) → 1.0 = same place, ~0.0 = antipodes.
Used as a bilateral diaspora proxy: nearby countries share migration flows.
"""
import math

# Capital city coordinates (lat, lon)
CAPITALS: dict[str, tuple[float, float]] = {
    "AL": (41.33, 19.82),  "AM": (40.18, 44.51),  "AT": (48.21, 16.37),
    "AU": (-35.28, 149.13),"AZ": (40.41, 49.87),  "BE": (50.85,  4.35),
    "BG": (42.70, 23.32),  "BY": (53.90, 27.57),  "CH": (46.95,  7.45),
    "CY": (35.17, 33.36),  "CZ": (50.08, 14.42),  "DE": (52.52, 13.41),
    "DK": (55.68, 12.57),  "EE": (59.44, 24.75),  "ES": (40.42, -3.70),
    "FI": (60.17, 24.94),  "FR": (48.86,  2.35),  "GB": (51.51, -0.13),
    "GE": (41.69, 44.83),  "GR": (37.98, 23.73),  "HR": (45.81, 15.97),
    "HU": (47.50, 19.05),  "IE": (53.35, -6.26),  "IL": (31.77, 35.21),
    "IS": (64.13,-21.93),  "IT": (41.90, 12.50),  "LT": (54.69, 25.28),
    "LU": (49.61,  6.13),  "LV": (56.95, 24.11),  "MD": (47.01, 28.86),
    "ME": (42.44, 19.26),  "MK": (41.99, 21.43),  "MT": (35.90, 14.51),
    "NO": (59.91, 10.75),  "PL": (52.23, 21.01),  "PT": (38.72, -9.14),
    "RO": (44.43, 26.10),  "RS": (44.82, 20.46),  "RU": (55.75, 37.62),
    "SE": (59.33, 18.07),  "SI": (46.05, 14.51),  "SM": (43.94, 12.46),
    "SK": (48.15, 17.11),  "TR": (39.93, 32.86),  "UA": (50.45, 30.52),
    "UK": (51.51, -0.13),  "XK": (42.67, 21.17),
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km."""
    R = 6371.0
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p)
         * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def geo_proximity(cc_from: str, cc_to: str) -> float:
    """
    Proximity score [0, 1].  1 = same location, decays with distance.
    Decay constant 1500 km ≈ Berlin-Athens distance.
    Missing countries → 0.1 (assume far).
    """
    a = CAPITALS.get(cc_from)
    b = CAPITALS.get(cc_to)
    if a is None or b is None:
        return 0.1
    dist = _haversine(a[0], a[1], b[0], b[1])
    return math.exp(-dist / 1500)


# Precomputed matrix for all pairs (cached on import)
_PROX: dict[tuple[str, str], float] = {}

def get_proximity(cc_from: str, cc_to: str) -> float:
    key = (cc_from, cc_to)
    if key not in _PROX:
        _PROX[key] = geo_proximity(cc_from, cc_to)
    return _PROX[key]
