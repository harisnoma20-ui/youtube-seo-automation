import json
import subprocess
import sys
import tempfile
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
    def test_accepts_vertical_video_up_to_50_seconds(self, run):
        run.return_value = ffprobe_result(50, 1080, 1920)

        result = uf.validate_short_eligibility("short.mp4")

        self.assertEqual(result["duration_seconds"], 50)
        self.assertEqual((result["width"], result["height"]), (1080, 1920))

    @patch("upload_features.subprocess.run")
    def test_rejects_short_over_50_seconds(self, run):
        run.return_value = ffprobe_result(51, 1080, 1920)

        with self.assertRaisesRegex(ValueError, "maximum 50 seconds"):
            uf.validate_short_eligibility("51-second.mp4")

    @patch("upload_features.subprocess.run")
    def test_accepts_small_encoder_duration_overrun(self, run):
        run.return_value = ffprobe_result(50.49, 1080, 1920)

        result = uf.validate_short_eligibility("50-second-export.mp4")

        self.assertEqual(result["duration_seconds"], 50.49)

    @patch("upload_features.subprocess.run")
    def test_rejects_landscape_video(self, run):
        run.return_value = ffprobe_result(50, 1920, 1080)

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
    def test_duplicate_hash_is_scoped_to_channel_and_persisted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = str(Path(temp_dir) / "hashes.json")
            media_path = Path(temp_dir) / "short.mp4"
            media_path.write_bytes(b"same exact video bytes")
            file_hash = uf.calculate_file_sha256(media_path)

            self.assertFalse(
                uf.is_duplicate_upload("medieval", file_hash, db_path)
            )
            uf.record_upload_hash("medieval", file_hash, db_path)
            self.assertTrue(
                uf.is_duplicate_upload("medieval", file_hash, db_path)
            )
            self.assertFalse(
                uf.is_duplicate_upload("other-channel", file_hash, db_path)
            )

    def test_natural_filename_order(self):
        names = ["10.mp4", "2.mp4", "1.mp4", "03 winter.mp4"]
        ordered = sorted(names, key=uf.natural_filename_key)
        self.assertEqual(ordered, ["1.mp4", "2.mp4", "03 winter.mp4", "10.mp4"])

    def test_topic_removes_queue_number_and_duplicate_extension(self):
        result = uf.topic_from_filename(
            "01 - What Did Medieval Peasants Eat.mp4.mp4"
        )
        self.assertEqual(result, "What Did Medieval Peasants Eat")

    def test_matching_content_brief_uses_same_numbered_base_name(self):
        class Files:
            def list(self, **_kwargs):
                return self

            def execute(self):
                return {"files": [
                    {"id": "wrong", "name": "02 - Winter.txt", "mimeType": "text/plain"},
                    {"id": "right", "name": "01 - Winter.md", "mimeType": "text/markdown"},
                ]}

        class Drive:
            def files(self):
                return Files()

        result = uf.find_matching_content_brief(Drive(), "folder", "01 - Winter.mp4")
        self.assertEqual(result["id"], "right")

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
