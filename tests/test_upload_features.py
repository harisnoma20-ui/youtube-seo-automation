import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
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
    def test_accepts_vertical_video_up_to_40_seconds(self, run):
        run.return_value = ffprobe_result(40, 1080, 1920)

        result = uf.validate_short_eligibility("short.mp4")

        self.assertEqual(result["duration_seconds"], 40)
        self.assertEqual((result["width"], result["height"]), (1080, 1920))

    @patch("upload_features.subprocess.run")
    def test_rejects_short_over_40_seconds(self, run):
        run.return_value = ffprobe_result(41, 1080, 1920)

        with self.assertRaisesRegex(ValueError, "maximum 40 seconds"):
            uf.validate_short_eligibility("41-second.mp4")

    @patch("upload_features.subprocess.run")
    def test_rejects_landscape_video(self, run):
        run.return_value = ffprobe_result(40, 1920, 1080)

        with self.assertRaisesRegex(ValueError, "square ya vertical"):
            uf.validate_short_eligibility("landscape.mp4")

    @patch("upload_features.subprocess.run")
    def test_accepts_long_video_over_60_seconds(self, run):
        run.return_value = ffprobe_result(61, 1920, 1080)

        result = uf.validate_long_eligibility("long.mp4")

        self.assertEqual(result["duration_seconds"], 61)

    @patch("upload_features.subprocess.run")
    def test_rejects_long_video_at_60_seconds(self, run):
        run.return_value = ffprobe_result(60, 1920, 1080)

        with self.assertRaisesRegex(ValueError, "60 seconds se zyada"):
            uf.validate_long_eligibility("60-second.mp4")


class QueueAndScheduleTests(unittest.TestCase):
    def test_natural_filename_order(self):
        names = ["10.mp4", "2.mp4", "1.mp4", "03 winter.mp4"]
        ordered = sorted(names, key=uf.natural_filename_key)
        self.assertEqual(ordered, ["1.mp4", "2.mp4", "03 winter.mp4", "10.mp4"])

    def test_topic_removes_queue_number_and_duplicate_extension(self):
        result = uf.topic_from_filename(
            "01 - What Did Medieval Peasants Eat.mp4.mp4"
        )
        self.assertEqual(result, "What Did Medieval Peasants Eat")

    def test_manual_run_uses_next_allowed_weekday(self):
        # Sunday 22:00 UTC; medieval long videos publish on Monday at 21:00.
        now = datetime(2026, 10, 18, 22, 0, tzinfo=timezone.utc)
        result = uf.calculate_next_publish_time(21, [0], now=now)
        self.assertEqual(result, "2026-10-19T21:00:00Z")

    def test_same_day_future_slot_is_used(self):
        # Tuesday 15:00 UTC; a Short can publish Tuesday at 21:00.
        now = datetime(2026, 10, 20, 15, 0, tzinfo=timezone.utc)
        result = uf.calculate_next_publish_time(21, [1, 3, 5], now=now)
        self.assertEqual(result, "2026-10-20T21:00:00Z")


if __name__ == "__main__":
    unittest.main()
