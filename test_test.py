import unittest
from test import test_rearrangement
import io
import sys

# filepath: /Users/geetika/space/cargo_manager/test_test.py

class TestCargoManager(unittest.TestCase):
    def test_rearrangement(self):
        # Capture the output during the test
        captured_output = io.StringIO()
        sys.stdout = captured_output

        # Run the test function
        test_rearrangement()

        # Restore stdout
        sys.stdout = sys.__stdout__

        # Check the captured output for expected debug prints
        output = captured_output.getvalue()
        self.assertIn("After placing Food Packet:", output)
        self.assertIn("After placing Oxygen Cylinder:", output)
        self.assertIn("Rearrangement test passed!", output)

if __name__ == '__main__':
    unittest.main()