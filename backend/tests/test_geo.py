import math
from app.utils.geo import calculate_distance, distance_decay

def test_calculate_distance():
    # Delhi to Gurgaon approx 30km straight line
    lat1, lon1 = 28.7041, 77.1025
    lat2, lon2 = 28.4595, 77.0266
    
    dist = calculate_distance(lat1, lon1, lat2, lon2)
    assert 25.0 < dist < 35.0

def test_distance_decay():
    # Distance 0 should yield 1.0
    assert distance_decay(0.0) == 1.0
    
    # Distance = scale_factor (e.g. 2.0) should yield 0.5
    assert distance_decay(2.0, scale_factor=2.0) == 0.5
    
    # Distance 10 (very far) should yield a small fraction, < 0.1
    assert distance_decay(10.0, scale_factor=2.0) < 0.1
    
    # Check monotonicity
    assert distance_decay(1.0) > distance_decay(2.0) > distance_decay(5.0)
