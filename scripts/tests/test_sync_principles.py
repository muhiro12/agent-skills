"""Behavior checks use disposable local remotes, never private records."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / 'sync_principles.py'
if not MODULE_PATH.exists():
    MODULE_PATH = Path(__file__).with_name('sync_principles.py')
spec = importlib.util.spec_from_file_location('sync_principles', MODULE_PATH)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def git(root, *args):
    return sync.run('git', '-C', str(root), *args)


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.remote = self.root / 'remote.git'
        self.work = self.root / 'records'
        self.other = self.root / 'other'
        sync.run('git', 'init', '--bare', str(self.remote))
        sync.run('git', 'clone', str(self.remote), str(self.work))
        git(self.work, 'checkout', '-b', 'main')
        self.identity(self.work)
        (self.work / 'README.md').write_text('# Records\n')
        git(self.work, 'add', 'README.md')
        git(self.work, 'commit', '-m', 'Initial records')
        git(self.work, 'push', 'origin', 'main')
        self.config = {'targets': {'example': {'enabled': True, 'push_on_update': True,
                      'path': str(self.work), 'remote': str(self.remote), 'repository': 'example/records'}}}
        self.repo = sync.Repository(self.config, 'example')
        self.private = patch.object(sync.Repository, 'private')
        self.private.start()
        self.addCleanup(self.private.stop)

    def identity(self, path):
        git(path, 'config', 'user.name', 'Fixture')
        git(path, 'config', 'user.email', 'fixture@example.invalid')

    def edit(self):
        (self.work / 'README.md').write_text('# Updated records\n')

    def review(self, base):
        manifest = self.root / 'review.json'
        manifest.write_text(json.dumps({'base': base, 'files': self.repo.hashes(self.repo.changed())}))
        return str(manifest)

    def advance_remote(self):
        sync.run('git', 'clone', '-b', 'main', str(self.remote), str(self.other))
        self.identity(self.other)
        (self.other / 'remote.md').write_text('# Remote update\n')
        git(self.other, 'add', 'remote.md')
        git(self.other, 'commit', '-m', 'Other device update')
        git(self.other, 'push', 'origin', 'main')
        return git(self.other, 'rev-parse', 'HEAD')

    def test_normal_update_and_readback(self):
        lease = self.repo.refresh(begin=True)
        self.edit()
        result = self.repo.finish(lease['token'], self.review(lease['base']), 'Update reviewed records')
        self.assertTrue(result['synchronized'])
        self.assertEqual(result['remote'], git(self.remote, 'rev-parse', 'main'))
        self.assertFalse(self.repo.lease.exists())

    def test_fast_forward_other_device(self):
        expected = self.advance_remote()
        self.assertEqual(self.repo.refresh()['base'], expected)
        self.assertTrue((self.work / 'remote.md').exists())
        self.assertEqual((self.work / 'remote.md').stat().st_mode & 0o777, 0o600)

    def test_existing_changes_preserved(self):
        self.edit()
        with self.assertRaises(sync.SyncError):
            self.repo.refresh(begin=True)
        self.assertEqual((self.work / 'README.md').read_text(), '# Updated records\n')

    def test_existing_unpushed_commit_not_adopted(self):
        self.edit()
        git(self.work, 'commit', '-am', 'Unrelated work')
        with self.assertRaises(sync.SyncError):
            self.repo.refresh()

    def test_concurrent_editor_and_wrong_token_rejected(self):
        self.repo.refresh(begin=True)
        with self.assertRaises(sync.SyncError):
            self.repo.refresh(begin=True)
        with self.assertRaises(sync.SyncError):
            self.repo.owned('another-task')

    def test_remote_advance_preserves_edits(self):
        lease = self.repo.refresh(begin=True)
        self.edit()
        expected = self.advance_remote()
        with self.assertRaises(sync.SyncError):
            self.repo.finish(lease['token'], self.review(lease['base']), 'Update records')
        self.assertEqual(git(self.remote, 'rev-parse', 'main'), expected)
        self.assertEqual(self.repo.head(), lease['base'])
        self.assertTrue(self.repo.changed())

    def test_changed_after_review_rejected(self):
        lease = self.repo.refresh(begin=True)
        self.edit()
        manifest = self.review(lease['base'])
        (self.work / 'README.md').write_text('# Another edit\n')
        with self.assertRaises(sync.SyncError):
            self.repo.finish(lease['token'], manifest, 'Update records')
        self.assertEqual(self.repo.head(), lease['base'])

    def test_unreviewed_file_and_staged_file_rejected(self):
        lease = self.repo.refresh(begin=True)
        self.edit()
        manifest = self.review(lease['base'])
        (self.work / 'unexpected.md').write_text('# Other task\n')
        with self.assertRaises(sync.SyncError):
            self.repo.finish(lease['token'], manifest, 'Update records')
        manifest = self.review(lease['base'])
        git(self.work, 'add', 'unexpected.md')
        with self.assertRaises(sync.SyncError):
            self.repo.finish(lease['token'], manifest, 'Update records')

    def test_offline_fetch_preserves_local_version(self):
        with patch.object(self.repo, 'fetch', side_effect=sync.SyncError('offline')):
            with self.assertRaises(sync.SyncError):
                self.repo.refresh(begin=True)
        self.assertFalse(self.repo.lease.exists())

    def test_offline_capture_can_be_published_when_remote_is_unchanged(self):
        lease = self.repo.refresh(begin=True, offline=True)
        self.assertFalse(lease['remote_checked'])
        self.edit()
        self.assertTrue(self.repo.finish(lease['token'], self.review(lease['base']), 'Offline capture')['synchronized'])

    def test_failed_push_retains_commit_and_retry(self):
        lease = self.repo.refresh(begin=True)
        self.edit()
        manifest = self.review(lease['base'])
        original = self.repo.git
        def fail_push(*args):
            if args[0] == 'push':
                raise sync.SyncError('offline')
            return original(*args)
        with patch.object(self.repo, 'git', side_effect=fail_push):
            with self.assertRaises(sync.SyncError):
                self.repo.finish(lease['token'], manifest, 'Update records')
        pending = json.loads(self.repo.lease.read_text())
        self.assertEqual(pending['commit'], self.repo.head())
        self.assertEqual(git(self.remote, 'rev-parse', 'main'), lease['base'])
        self.assertTrue(self.repo.finish(lease['token'], manifest, 'Unused on retry')['synchronized'])

    def test_commit_hook_cannot_publish_unreviewed_content_even_on_retry(self):
        hook = self.work / '.git/hooks/pre-commit'
        hook.write_text('#!/bin/sh\nprintf "Hook change\\n" > hook.md\ngit add hook.md\n')
        hook.chmod(0o700)
        lease = self.repo.refresh(begin=True)
        self.edit()
        manifest = self.review(lease['base'])
        for attempt in range(2):
            with self.assertRaises(sync.SyncError):
                self.repo.finish(lease['token'], manifest, 'Update records')
        self.assertEqual(git(self.remote, 'rev-parse', 'main'), lease['base'])

    def test_symlink_and_missing_history_rejected(self):
        (self.work / 'linked.md').symlink_to(self.root / 'outside.md')
        with self.assertRaises(sync.SyncError):
            self.repo.hashes(['linked.md'])
        with self.assertRaises(sync.SyncError):
            self.repo.validate(['principles/meta/current.md'])

    def test_disabled_and_wrong_root_branch_remote_rejected(self):
        settings = self.config['targets']['example']
        for field, value in [('enabled', False), ('remote', 'another'), ('path', str(self.work / 'sub'))]:
            original = settings[field]
            settings[field] = value
            with self.assertRaises(sync.SyncError):
                sync.Repository(self.config, 'example')
            settings[field] = original
        git(self.work, 'checkout', '-b', 'other')
        with self.assertRaises(sync.SyncError):
            sync.Repository(self.config, 'example')

    def test_public_visibility_rejected(self):
        self.private.stop()
        self.repo.settings['remote'] = 'https://github.com/example/records.git'
        with patch.object(sync, 'run', return_value='public'):
            with self.assertRaises(sync.SyncError):
                self.repo.private()


if __name__ == '__main__':
    unittest.main()
