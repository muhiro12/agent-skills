"""Verify compact status without starting Claude or reading its stream."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_claude_runner import runner


class CompactStatusTests(unittest.TestCase):
    def test_reports_checkpoint_without_reading_stream_or_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory).resolve()
            folder = task / 'rounds' / '001'
            folder.mkdir(parents=True)
            (task / 'runner-state.json').write_text(json.dumps({
                'task_dir': str(task), 'round_count': 1, 'status': 'running',
                'session_id': 'fixture'}))
            (folder / 'stdout.jsonl').write_text('invalid JSON must not be parsed')
            checkpoint = folder / 'checkpoint.md'
            checkpoint.write_text('private detailed evidence')
            with patch.object(runner, 'execute', side_effect=AssertionError('must not launch')):
                result = runner.compact_status(task)
            self.assertEqual(result['recorded_status'], 'running')
            self.assertEqual(result['checkpoint'], str(checkpoint))
            self.assertNotIn('private detailed evidence', json.dumps(result))
            self.assertIsNone(result['summary'])
            checkpoint.unlink()
            self.assertIsNone(runner.compact_status(task)['checkpoint'])

    def test_rejects_checkpoint_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory).resolve()
            folder = task / 'rounds' / '001'
            folder.mkdir(parents=True)
            (task / 'runner-state.json').write_text(json.dumps({
                'task_dir': str(task), 'round_count': 1, 'status': 'running'}))
            (folder / 'checkpoint.md').symlink_to(task / 'runner-state.json')
            with self.assertRaises(runner.Refusal):
                runner.compact_status(task)

    def test_rejects_invalid_state_and_missing_round(self):
        with tempfile.TemporaryDirectory() as directory:
            task = Path(directory).resolve()
            state = task / 'runner-state.json'
            state.write_text('[]')
            with self.assertRaisesRegex(runner.Refusal, 'JSON object'):
                runner.compact_status(task)
            state.write_text(json.dumps({
                'task_dir': str(task), 'round_count': 1, 'status': 'running'}))
            with self.assertRaisesRegex(runner.Refusal, 'round is unavailable'):
                runner.compact_status(task)

    def test_rejects_task_directory_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            task = root / 'task'
            task.mkdir()
            linked_task = root / 'linked-task'
            linked_task.symlink_to(task, target_is_directory=True)
            with self.assertRaisesRegex(runner.Refusal, 'symbolic link'):
                runner.compact_status(linked_task)
