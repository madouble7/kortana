import time
import unittest

from kortana.utils.timestamp_utils import get_iso_timestamp


class TestTimestampUtils(unittest.TestCase):
    def test_output_is_string(self):
        """Test that the output of get_iso_timestamp is a string."""
        timestamp = get_iso_timestamp()
        self.assertIsInstance(timestamp, str)

    def test_output_iso_8601_format(self):
        """Test that the output string matches the ISO 8601 UTC pattern."""
        timestamp = get_iso_timestamp()
        # Basic structure check: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS.ffffffZ
        self.assertTrue(timestamp.endswith("Z"))
        # Further checks could involve regex for stricter validation if needed
        # A simpler check for presence of basic components
        self.assertIn("-", timestamp)  # Check for date separators
        self.assertIn("T", timestamp)  # Check for date-time separator
        self.assertIn(":", timestamp)  # Check for time separators

    def test_distinct_timestamps_over_time(self):
        """Test that two calls made at least one second apart yield distinct timestamps."""
        timestamp1 = get_iso_timestamp()
        time.sleep(1.1)  # Ensure at least one second passes
        timestamp2 = get_iso_timestamp()
        self.assertNotEqual(timestamp1, timestamp2)


if __name__ == "__main__":
    unittest.main()
