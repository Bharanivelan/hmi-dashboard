import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from siyi_protocol import SiyiCameraProtocol


class SiyiCameraProtocolTests(unittest.TestCase):
    def test_send_center_method_exists(self):
        cam = SiyiCameraProtocol(camera_ip="127.0.0.1", camera_port=37260)
        self.assertTrue(callable(getattr(cam, "send_center", None)))


if __name__ == "__main__":
    unittest.main()
