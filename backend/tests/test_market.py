import unittest

from app.services.location.radius import bounded_distance_decay, radius_band


class RadiusTests(unittest.TestCase):
    def test_supported_bands_are_explicit(self) -> None:
        self.assertEqual(radius_band(0), "0-2 km")
        self.assertEqual(radius_band(2), "0-2 km")
        self.assertEqual(radius_band(4.9), "2-5 km")
        self.assertEqual(radius_band(8), "5-10 km")
        self.assertIsNone(radius_band(10.1))

    def test_distance_decay_is_bounded_and_monotonic(self) -> None:
        self.assertEqual(bounded_distance_decay(0), 1)
        self.assertEqual(bounded_distance_decay(10), 0)
        self.assertGreater(bounded_distance_decay(2), bounded_distance_decay(8))


if __name__ == "__main__":
    unittest.main()