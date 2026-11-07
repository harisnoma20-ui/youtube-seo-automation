import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import seo_automation as sa


class ChannelSafetyTests(unittest.TestCase):
    def context(self, prefix='WILDLIFE_'):
        values = {prefix + key: key for key in (
            'YOUTUBE_API_KEY', 'YOUTUBE_CHANNEL_ID', 'YOUTUBE_OAUTH_CLIENT_ID',
            'YOUTUBE_OAUTH_CLIENT_SECRET', 'YOUTUBE_OAUTH_REFRESH_TOKEN',
            'DRIVE_SHORTS_TOUPLOAD_FOLDER_ID', 'DRIVE_SHORTS_UPLOADED_FOLDER_ID',
            'DRIVE_LONG_TOUPLOAD_FOLDER_ID', 'DRIVE_LONG_UPLOADED_FOLDER_ID')}
        with patch.dict(os.environ, values, clear=True):
            return sa.build_channel_context({'name': 'born_to_wild', 'secret_prefix': prefix})

    def test_prefix_never_falls_back_to_other_channel(self):
        with patch.dict(os.environ, {'YOUTUBE_OAUTH_REFRESH_TOKEN': 'wrong'}, clear=True):
            ctx = sa.build_channel_context({'name': 'wildlife', 'secret_prefix': 'WILDLIFE_'})
        self.assertIsNone(ctx['oauth_refresh_token'])
        self.assertEqual(ctx['tracking_file'], 'tracking_sheet_wildlife.xlsx')

    def test_wrong_oauth_channel_blocks_processing_before_research(self):
        youtube = MagicMock()
        youtube.channels.return_value.list.return_value.execute.return_value = {'items': [{'id': 'wrong'}]}
        with patch.object(sa, 'build', return_value=youtube), patch.object(sa, 'get_trending_keywords') as trends:
            with self.assertRaisesRegex(ValueError, 'does not match'):
                sa.process_channel(self.context())
            trends.assert_not_called()
            youtube.videos.assert_not_called()

    def test_handle_must_resolve_to_expected_channel(self):
        ctx = self.context()
        ctx['channel_handle'] = '@borntowild-u9b'
        youtube = MagicMock()
        youtube.channels.return_value.list.return_value.execute.side_effect = [
            {'items': [{'id': ctx['youtube_channel_id']}]}, {'items': [{'id': 'other'}]}]
        with self.assertRaisesRegex(ValueError, 'does not match @'):
            sa.verify_youtube_identity(youtube, ctx)

    def test_preflight_missing_secrets_fails_before_network(self):
        with patch.dict(os.environ, {}, clear=True):
            ctx = sa.build_channel_context({'name': 'wildlife', 'secret_prefix': 'WILDLIFE_'})
        with patch.object(sa, 'build') as build:
            with self.assertRaisesRegex(ValueError, 'WILDLIFE_YOUTUBE_OAUTH_REFRESH_TOKEN'):
                sa.preflight_channel(ctx)
            build.assert_not_called()

    @patch.object(sa, 'GROQ_API_KEY', 'test-only')
    def test_preflight_is_read_only_and_checks_all_folders(self):
        ctx = self.context()
        youtube, drive = MagicMock(), MagicMock()
        youtube.channels.return_value.list.return_value.execute.return_value = {
            'items': [{'id': ctx['youtube_channel_id'], 'snippet': {'title': 'Born to Wild'}}]}
        drive.files.return_value.get.return_value.execute.return_value = {
            'mimeType': 'application/vnd.google-apps.folder', 'capabilities': {'canAddChildren': True}}
        drive.files.return_value.list.return_value.execute.return_value = {'files': []}
        with patch.object(sa, 'build', side_effect=[youtube, youtube, drive]):
            sa.preflight_channel(ctx)
        self.assertEqual(drive.files.return_value.get.call_count, 4)
        youtube.videos.assert_not_called()
        drive.files.return_value.update.assert_not_called()
        drive.files.return_value.get_media.assert_not_called()

    @patch.object(sa, 'GROQ_API_KEY', 'test-only')
    def test_shared_source_destination_is_rejected(self):
        ctx = self.context()
        ctx['drive_long_uploaded'] = ctx['drive_long_toupload']
        with patch.object(sa, 'build') as build:
            with self.assertRaisesRegex(ValueError, 'distinct'):
                sa.preflight_channel(ctx)
            build.assert_not_called()

    def test_preflight_cli_does_not_call_normal_processing(self):
        channels = [{'name': 'medieval'}, {'name': 'wildlife'}]
        with patch.object(sys, 'argv', ['seo', '--preflight']), patch.object(sa, 'load_channels', return_value=channels), patch.object(sa, 'preflight_channel') as check, patch.object(sa, 'process_channel') as process:
            with self.assertRaises(SystemExit) as result:
                sa.main()
        self.assertEqual(result.exception.code, 0)
        self.assertEqual(check.call_count, 2)
        process.assert_not_called()

    def test_failed_preflight_continues_other_channel_and_returns_failure(self):
        with patch.object(sys, 'argv', ['seo', '--preflight']), patch.object(sa, 'load_channels', return_value=[{'name': 'a'}, {'name': 'b'}]), patch.object(sa, 'preflight_channel', side_effect=[ValueError('missing'), None]) as check:
            with self.assertRaises(SystemExit) as result:
                sa.main()
        self.assertEqual(result.exception.code, 1)
        self.assertEqual(check.call_count, 2)

    @patch.object(sa, 'GROQ_API_KEY', 'test-only')
    def test_drive_move_failure_records_hash_first_and_fails_run(self):
        from contextlib import ExitStack
        ctx = self.context()
        ctx['shorts_upload_days'] = '0,1,2,3,4,5,6'
        ctx['long_upload_days'] = ''
        events = []
        replacements = {
            'verify_youtube_identity': MagicMock(),
            'get_trending_keywords': MagicMock(return_value=['wildlife']),
            'get_recent_videos': MagicMock(return_value=[]),
            'generate_seo_content_for_video': MagicMock(return_value={'title': 'Wolf', 'description': 'Journey', 'tags': []}),
            'log_to_tracking_sheet': MagicMock(),
            'build': MagicMock(),
        }
        uploads = {
            'list_new_drive_videos': MagicMock(return_value=[{'id': 'file', 'name': 'wolf.mp4'}]),
            'download_drive_file': MagicMock(return_value='temp.mp4'),
            'validate_short_eligibility': MagicMock(return_value={'duration_seconds': 40, 'width': 1080, 'height': 1920}),
            'calculate_file_sha256': MagicMock(return_value='hash'),
            'is_duplicate_upload': MagicMock(return_value=False),
            'find_matching_content_brief': MagicMock(return_value=None),
            'upload_video_to_youtube': MagicMock(return_value='uploaded-id'),
            'record_upload_hash': MagicMock(side_effect=lambda *a: events.append('hash')),
            'move_drive_file': MagicMock(side_effect=lambda *a: (events.append('move'), (_ for _ in ()).throw(RuntimeError('move failed')))),
            'cleanup_downloaded_file': MagicMock(),
        }
        with ExitStack() as stack:
            for key, value in replacements.items():
                stack.enter_context(patch.object(sa, key, value))
            for key, value in uploads.items():
                stack.enter_context(patch.object(sa.uf, key, value))
            for key, value in {'get_winning_keywords': [], 'check_trending_surge': [], 'track_competitor_titles': [], 'generate_community_post_ideas': []}.items():
                stack.enter_context(patch.object(sa.gf, key, return_value=value))
            with self.assertRaisesRegex(RuntimeError, 'Upload jobs failed'):
                sa.process_channel(ctx)
        self.assertEqual(events, ['hash', 'move'])
        replacements['log_to_tracking_sheet'].assert_called_once()
        uploads['upload_video_to_youtube'].assert_called_once()

    def test_born_to_wild_stays_disabled_pending_credentials(self):
        cfg = json.loads((Path(__file__).resolve().parents[1] / 'channels_config.json').read_text())
        wildlife = next(c for c in cfg['channels'] if c['name'] == 'born_to_wild')
        self.assertFalse(wildlife['enabled'])
        self.assertEqual(wildlife['target_audience_geos'], 'US,GB,CA,AU')
        self.assertEqual(wildlife['secret_prefix'], 'WILDLIFE_')


if __name__ == '__main__':
    unittest.main()
