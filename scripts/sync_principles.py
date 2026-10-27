#!/usr/bin/env python3
"""Opt-in synchronization of private principle records using ordinary Git."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid


class SyncError(Exception):
    pass


def run(*args, cwd=None):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, umask=0o077)
    if result.returncode:
        raise SyncError(f'{args[0]} failed: {result.stderr.strip()}')
    return result.stdout.strip()


def write_json(path, value):
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex)
    try:
        with temporary.open('x') as stream:
            os.chmod(temporary, 0o600)
            json.dump(value, stream, indent=2)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class Repository:
    def __init__(self, config, target):
        self.settings = config['targets'][target]
        if self.settings.get('enabled') is not True:
            raise SyncError('Synchronization is disabled')
        self.root = Path(self.settings['path']).expanduser()
        if self.root != self.root.resolve():
            raise SyncError('Use the canonical record path, without symlinks')
        if self.git('rev-parse', '--show-toplevel') != str(self.root):
            raise SyncError('Unexpected Git root')
        if self.git('branch', '--show-current') != 'main':
            raise SyncError('Expected main')
        if self.git('remote', 'get-url', '--all', 'origin') != self.settings['remote']:
            raise SyncError('Unexpected fetch remote')
        if self.git('remote', 'get-url', '--push', '--all', 'origin') != self.settings['remote']:
            raise SyncError('Unexpected push remote')
        self.state = Path(self.git('rev-parse', '--absolute-git-dir')) / 'principles-sync'
        self.state.mkdir(mode=0o700, exist_ok=True)
        self.lease = self.state / 'lease.json'

    def git(self, *args):
        return run('git', '-C', str(self.root), *args)

    @contextlib.contextmanager
    def lock(self):
        with (self.state / 'command.lock').open('a') as stream:
            os.chmod(stream.name, 0o600)
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise SyncError('Another synchronization command is running') from error
            yield

    def private(self):
        name = self.settings['repository']
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', name):
            raise SyncError('Invalid repository identity')
        expected = {f'https://github.com/{name}.git', f'git@github.com:{name}.git'}
        if self.settings['remote'] not in expected:
            raise SyncError('Remote does not match configured GitHub repository')
        visibility = run('gh', 'api', f'repos/{name}', '--jq', '.visibility')
        if visibility != 'private':
            raise SyncError('Private visibility could not be confirmed')

    def head(self):
        return self.git('rev-parse', 'HEAD')

    def changed(self):
        tracked = self.git('diff', '--name-only', 'HEAD', '-z').split('\0')
        untracked = self.git('ls-files', '--others', '--exclude-standard', '-z').split('\0')
        return sorted(set(filter(None, tracked + untracked)))

    def fetch(self):
        self.private()
        self.git('fetch', '--no-tags', 'origin', 'refs/heads/main')
        return self.git('rev-parse', 'FETCH_HEAD')

    def refresh(self, begin=False, offline=False):
        if self.lease.exists():
            raise SyncError('An edit lease already exists; inspect it before recovery')
        if self.changed() or self.git('diff', '--cached', '--name-only'):
            raise SyncError('Existing changes require their owner to finish or review them')
        if offline:
            if not begin or self.head() != self.git('rev-parse', 'refs/remotes/origin/main'):
                raise SyncError('Offline editing requires a clean last-synchronized base')
            result = {'base': self.head(), 'remote': None, 'remote_checked': False, 'token': uuid.uuid4().hex}
            write_json(self.lease, result)
            return result
        remote = self.fetch()
        if self.git('rev-list', '--count', remote + '..HEAD') != '0':
            raise SyncError('Existing local commits or divergence require explicit review')
        self.git('merge', '--ff-only', remote)
        result = {'base': self.head(), 'remote': remote}
        if begin:
            result['token'] = uuid.uuid4().hex
            write_json(self.lease, result)
        return result

    def owned(self, token):
        if not self.lease.exists():
            raise SyncError('No active edit lease')
        value = json.loads(self.lease.read_text())
        if not token or token != value['token']:
            raise SyncError('Edit lease belongs to another task')
        return value

    def hashes(self, paths):
        result = {}
        for name in paths:
            relative = Path(name)
            if relative.is_absolute() or '..' in relative.parts or '.git' in relative.parts:
                raise SyncError('Invalid record path')
            path = self.root / relative
            if any(p.is_symlink() for p in [path, *path.parents]):
                raise SyncError('Symlinks are not record files')
            if not (name == '.gitignore' or path.suffix == '.md'):
                raise SyncError('Only Markdown records and .gitignore can be synchronized')
            result[name] = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        return result

    def validate(self, paths):
        self.git('diff', '--check')
        self.git('diff', '--cached', '--check')
        if any(p.startswith(('principles/', 'design-guides/')) for p in paths):
            if 'evolution-log.md' not in paths:
                raise SyncError('Record changes require a corresponding evolution entry')
        for name in paths:
            path = self.root / name
            if not path.exists() or path.suffix != '.md':
                continue
            content = path.read_text()
            for link in re.findall(r'\]\(([^\s)]+)\)', content):
                if re.match(r'[a-zA-Z]+:', link) or link.startswith('#'):
                    continue
                target = (path.parent / link.split('#')[0]).resolve()
                if not target.is_relative_to(self.root) or not target.exists():
                    raise SyncError(f'Unresolved local link in {name}: {link}')
        index = self.root / 'current-principles.md'
        if index.exists():
            for name in re.findall(r'`(principles/[^`]+/current\.md)`', index.read_text()):
                if not (self.root / name).is_file():
                    raise SyncError(f'Missing indexed domain: {name}')

    def verify_commit(self, lease):
        commit = lease['commit']
        if self.git('rev-parse', commit + '^') != lease['base']:
            raise SyncError('Committed parent differs from reviewed base')
        changed = sorted(filter(None, self.git('diff', '--name-only', '-z', lease['base'], commit).split('\0')))
        if changed != sorted(lease['files']):
            raise SyncError('Committed file set differs from review')
        for name, expected in lease['files'].items():
            if expected is None:
                if self.git('ls-tree', commit, '--', name):
                    raise SyncError('Reviewed deletion remains in commit')
                continue
            result = subprocess.run(['git', '-C', str(self.root), 'cat-file', 'blob', commit + ':' + name],
                                    capture_output=True)
            if result.returncode or hashlib.sha256(result.stdout).hexdigest() != expected:
                raise SyncError('Committed bytes differ from review')

    def finish(self, token, manifest, message):
        if self.settings.get('push_on_update') is not True:
            raise SyncError('Commit and push are not enabled in this host configuration')
        lease = self.owned(token)
        remote = self.fetch()
        if 'commit' in lease:
            commit = lease['commit']
            if self.head() != commit or self.changed():
                raise SyncError('The pending commit or working tree has changed')
            if remote not in (lease['base'], commit):
                raise SyncError('Remote advanced; preserve the pending commit and reconcile explicitly')
        else:
            if self.head() != lease['base'] or remote != lease['base']:
                raise SyncError('Edit base changed; preserve edits and reconcile explicitly')
            if self.git('diff', '--cached', '--name-only'):
                raise SyncError('Pre-staged changes require explicit review')
            review = json.loads(Path(manifest).read_text())
            paths = sorted(review['files'])
            if review.get('base') != lease['base'] or not paths or paths != self.changed():
                raise SyncError('Reviewed manifest does not match the base and complete changed file set')
            if self.hashes(paths) != review['files']:
                raise SyncError('Records changed after review')
            self.validate(paths)
            self.git('add', '--', *paths)
            self.git('commit', '-m', message)
            commit = self.head()
            lease['commit'] = commit
            lease['files'] = review['files']
            write_json(self.lease, lease)
        self.verify_commit(lease)
        if self.head() != commit or self.changed():
            raise SyncError('Local state changed before push')
        self.git('push', '--no-follow-tags', '--recurse-submodules=no', 'origin', f'{commit}:refs/heads/main')
        observed = self.git('ls-remote', self.settings['remote'], 'refs/heads/main').split()[0]
        if observed != commit:
            raise SyncError('Remote read-back differs; do not report synchronized')
        self.lease.unlink()
        return {'local': commit, 'remote': observed, 'synchronized': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('action', choices=['status', 'refresh', 'begin', 'finish', 'abort'])
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--token')
    parser.add_argument('--manifest')
    parser.add_argument('--message')
    args = parser.parse_args()
    try:
        repo = Repository(json.loads(Path(args.config).expanduser().read_text()), args.target)
        with repo.lock():
            if args.action == 'status':
                result = {'local': repo.head(), 'changed': repo.changed(), 'remote_checked': False,
                          'lease': json.loads(repo.lease.read_text()) if repo.lease.exists() else None}
            elif args.action in ('refresh', 'begin'):
                result = repo.refresh(begin=args.action == 'begin', offline=args.offline)
            elif args.action == 'abort':
                repo.owned(args.token)
                repo.lease.unlink()
                result = {'lease_released': True, 'changes_preserved': True}
            else:
                if not args.manifest or not args.message:
                    raise SyncError('finish requires --manifest and --message')
                result = repo.finish(args.token, args.manifest, args.message)
        print(json.dumps(result, indent=2))
    except (SyncError, OSError, ValueError, KeyError) as error:
        print(json.dumps({'synchronized': False, 'error': str(error)}), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
