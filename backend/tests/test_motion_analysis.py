import unittest

from backend.motion_analysis import analyze_motion


class MotionAnalysisTests(unittest.TestCase):
    def test_calibrating_when_samples_are_insufficient(self):
        result = analyze_motion([{"rssi": -60}] * 4)

        self.assertFalse(result["ready"])
        self.assertEqual(result["motion_state"], "CALIBRATING")
        self.assertEqual(result["sample_count"], 4)

    def test_stable_signal_is_no_motion(self):
        result = analyze_motion([{"rssi": -60}] * 20)

        self.assertTrue(result["ready"])
        self.assertEqual(result["motion_state"], "NO_MOTION")
        self.assertLess(result["motion_score"], 0.38)

    def test_strong_signal_variation_is_motion(self):
        samples = [{"rssi": -50 if index % 2 == 0 else -70} for index in range(20)]
        result = analyze_motion(samples)

        self.assertTrue(result["ready"])
        self.assertEqual(result["motion_state"], "MOTION")
        self.assertGreaterEqual(result["motion_score"], 0.62)
        self.assertGreater(result["features"]["rssi_std"], 5)


if __name__ == "__main__":
    unittest.main()
