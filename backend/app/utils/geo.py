import math

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees) in kilometers.
    """
    # Convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def distance_decay(distance_km: float, scale_factor: float = 2.0) -> float:
    """
    Bounded distance decay function.
    Instead of 1/distance, we use 1 / (1 + (distance / scale_factor)^2).
    This ensures distance 0 gives exactly 1.0 (100% relevance),
    and slowly decays as distance increases.
    """
    return 1.0 / (1.0 + (distance_km / scale_factor) ** 2)
