import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import upload_features as uf


def ffprobe_result(duration, width, height):
    return subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=json.dumps(
            {
                "streams": [{"width": width, "height": height}],
                "format": {"duration": str(duration)},
            }
        ),
        stderr="",
    )


class ShortEligibilityTests(unittest.TestCase):
    @patch("upload_features.subprocess.run")
    def test_accepts_vertical_video_up_to_three_minutes(self, run):
        run.return_value = ffprobe_result(180, 1080, 1920)

        result = uf.validate_short_eligibility("short.mp4")

        self.assertEqual(result["duration_seconds"], 180)
        self.assertEqual((result["width"], result["height"]), (1080, 1920))

    @patch("upload_features.subprocess.run")
    def test_rejects_video_over_three_minutes(self, run):
        run.return_value = ffprobe_result(600, 1080, 1920)

        with self.assertRaisesRegex(ValueError, "maximum duration 180 seconds"):
            uf.validate_short_eligibility("ten-minute.mp4")

    @patch("upload_features.subprocess.run")
    def test_rejects_landscape_video(self, run):
        run.return_value = ffprobe_result(60, 1920, 1080)

        with self.assertRaisesRegex(ValueError, "square ya vertical"):
            uf.validate_short_eligibility("landscape.mp4")


if __name__ == "__main__":
    unittest.main()
