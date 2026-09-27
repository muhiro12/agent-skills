#!/usr/bin/env python3
"""Execute one bounded Claude turn; the active Codex task reviews the return."""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid

SKILL = Path(__file__).resolve().parents[1] / 'SKILL.md'
DEFAULT_LIMITS = {'timeout': 600, 'max_turns': 20, 'max_budget_usd': 3, 'max_rounds': 4}
VISIBLE_FLAGS = ('--print', '--output-format', '--verbose', '--model', '--effort',
                 '--max-budget-usd', '--permission-mode', '--permission-prompts',
                 '--session-id', '--resume', '--allowedTools', '--add-dir')
OFFICIAL_ENDPOINT = 'https://api.anthropic.com'
ENDPOINT_ENV = ('ANTHROPIC_BASE_URL', 'ANTHROPIC_API_URL')
AUTH_KEYS = ('loggedIn', 'authMethod', 'apiProvider', 'subscriptionType')
AUTH_ENV = ('ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN', 'ANTHROPIC_BASE_URL',
            'ANTHROPIC_API_URL', 'ANTHROPIC_CUSTOM_HEADERS', 'ANTHROPIC_PROFILE',
            'CLAUDE_CODE_OAUTH_TOKEN', 'CLAUDE_CODE_USE_BEDROCK',
            'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY',
            'AWS_BEARER_TOKEN_BEDROCK')


class Refusal(Exception):
    pass


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError('must be positive and finite')
    return number


def count(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('must be a positive integer')
    return number


def checked(path):
    if path.is_symlink():
        raise Refusal(f'refusing symbolic link: {path}')
    return path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def new_file(path, data):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(checked(path), flags, 0o600), 'wb') as file:
        file.write(data)


def atomic_json(path, value):
    checked(path)
    fd, name = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as file:
            json.dump(value, file, indent=2, ensure_ascii=False)
            file.write('\n')
        checked(path)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextlib.contextmanager
def locked(path):
    flags = os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(checked(path), flags, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Refusal(f'another runner holds {path}')
        yield
    finally:
        os.close(fd)


def executable(explicit=None, desktop_root=None):
    if explicit:
        found = shutil.which(explicit)
        if not found:
            raise Refusal('the explicit Claude executable is unavailable')
        return str(Path(found).resolve())
    found = shutil.which('claude')
    if found:
        return str(Path(found).resolve())
    root = desktop_root or Path.home() / 'Library/Application Support/Claude/claude-code'
    candidates = []
    if root.is_dir():
        for folder in root.iterdir():
            binary = folder / 'claude.app/Contents/MacOS/claude'
            if re.fullmatch(r'\d+(?:\.\d+)*', folder.name) and binary.is_file() and os.access(binary, os.X_OK):
                candidates.append((tuple(map(int, folder.name.split('.'))), binary))
    if not candidates:
        raise Refusal('no Claude CLI found; use --claude-bin')
    # Desktop discovery is a local adapter, not an official stable path contract.
    return str(max(candidates)[1].resolve())


def capture(command, cwd=None, timeout=30):
    return subprocess.run(command, cwd=cwd, stdin=subprocess.DEVNULL,
                          capture_output=True, timeout=timeout, check=False)


def probe(binary, cwd, timeout=30):
    problems = []
    overrides = sorted(name for name in AUTH_ENV if os.environ.get(name)
                       and not (name in ENDPOINT_ENV and os.environ[name] == OFFICIAL_ENDPOINT))
    if overrides:
        problems.append('alternate credential/provider environment: ' + ', '.join(overrides))
    if problems:
        return {'executable': binary, 'eligible': False, 'problems': problems}
    version = capture([binary, '--version'], cwd, timeout)
    help_result = capture([binary, '--help'], cwd, timeout)
    auth_result = capture([binary, 'auth', 'status', '--json'], cwd, timeout)
    if any(item.returncode for item in (version, help_result, auth_result)):
        problems.append('a CLI probe exited with an error')
    match = re.search(rb'\d+\.\d+\.\d+', version.stdout)
    if not match:
        problems.append('unrecognized CLI version')
    missing = [flag for flag in VISIBLE_FLAGS if flag.encode() not in help_result.stdout]
    if missing:
        problems.append('missing visible CLI flags: ' + ', '.join(missing))
    try:
        payload = json.loads(auth_result.stdout)
        auth = {key: payload.get(key) for key in AUTH_KEYS}
    except (ValueError, AttributeError):
        auth = dict.fromkeys(AUTH_KEYS)
    # Raw auth output, email, account identifiers and tokens are never stored.
    auth = {key: value if isinstance(value, bool) or value is None or
            (isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9 ._-]{1,64}', value))
            else None for key, value in auth.items()}
    if not (auth['loggedIn'] is True and auth['authMethod'] == 'claude.ai'
            and auth['apiProvider'] == 'firstParty' and auth['subscriptionType']):
        problems.append('a logged-in first-party claude.ai subscription is required')
    return {'executable': binary, 'version': match.group().decode() if match else None,
            'auth': auth, 'eligible': not problems, 'problems': problems,
            'documented_hidden_flags': ['--max-turns']}


def git(checkout, *args):
    result = capture(['git', '--no-pager', '-C', str(checkout), *args])
    if result.returncode:
        raise Refusal('Git inspection failed: ' + ' '.join(args))
    return result.stdout


def snapshot(checkout, folder, label):
    result = {'head': git(checkout, 'rev-parse', 'HEAD').decode().strip(),
              'status': git(checkout, 'status', '--porcelain=v1', '-z').decode(errors='replace'),
              'untracked': {}}
    for name, arguments in (('unstaged', []), ('staged', ['--cached'])):
        patch = git(checkout, 'diff', '--no-ext-diff', '--no-textconv', '--binary', *arguments)
        path = folder / f'{label}-{name}.patch'
        new_file(path, patch)
        result[name] = {'sha256': digest(patch), 'path': str(path)}
    paths = git(checkout, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0')
    for raw in filter(None, paths):
        name = os.fsdecode(raw)
        path = checkout / name
        if len(result['untracked']) >= 200:
            result['untracked_truncated'] = True
            break
        if path.is_symlink():
            result['untracked'][name] = {'symlink': os.readlink(path)}
        elif path.is_file() and path.stat().st_size <= 8 * 1024 * 1024:
            result['untracked'][name] = {'sha256': digest(path.read_bytes())}
        else:
            result['untracked'][name] = {'not_hashed': True}
    atomic_json(folder / f'git-{label}.json', result)
    return result


def stop_group(process, grace=2):
    """Stop this spawned process group, including children outliving its leader."""
    group = process.pid  # Popen uses start_new_session=True.
    if group == os.getpgrp():
        raise Refusal('refusing to signal the coordinator process group')
    try:
        os.killpg(group, signal.SIGTERM)
    except ProcessLookupError:
        process.wait()
        return
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        process.poll()
        try:
            os.killpg(group, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    try:
        os.killpg(group, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)


def execute(command, checkout, folder, timeout):
    # Keep the files open from exclusive creation through process completion.
    with contextlib.ExitStack() as stack:
        inp = stack.enter_context((folder / 'prompt.md').open('rb'))
        outputs = []
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
        for name in ('stdout.jsonl', 'stderr.log'):
            fd = os.open(checked(folder / name), flags, 0o600)
            outputs.append(stack.enter_context(os.fdopen(fd, 'wb')))
        # Defer interruption during Popen so its PID cannot be lost mid-launch.
        pending = []
        signals = (signal.SIGINT, signal.SIGTERM)
        previous = {number: signal.getsignal(number) for number in signals}
        for number in signals:
            signal.signal(number, lambda signum, frame: pending.append(signum))
        process, status, code = None, 'completed', None
        try:
            process = subprocess.Popen(command, cwd=checkout, stdin=inp,
                                       stdout=outputs[0], stderr=outputs[1], start_new_session=True)
            for number, handler in previous.items():
                signal.signal(number, handler)
            if pending:
                raise KeyboardInterrupt()
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            status = 'timeout'
        except KeyboardInterrupt:
            status = 'interrupted'
        finally:
            for number in signals:
                signal.signal(number, lambda signum, frame: pending.append(signum))
            try:
                if process is not None:
                    stop_group(process)
            finally:
                for number, handler in previous.items():
                    signal.signal(number, handler)
        return {'status': status, 'exit_code': code if code is not None else process.returncode}


def evaluate(path, process, session, checkout, mode):
    events, problems = [], []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError()
            events.append(event)
        except ValueError:
            problems.append('malformed stream JSON')
    inits = [e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init']
    finals = [e for e in events if e.get('type') == 'result']
    init = inits[0] if len(inits) == 1 else {}
    result = finals[0] if len(finals) == 1 else {}
    if len(inits) != 1 or len(finals) != 1:
        problems.append('expected exactly one init and final result')
    if process != {'status': 'completed', 'exit_code': 0}:
        problems.append('Claude did not exit successfully')
    if result.get('is_error') is not False or result.get('subtype') != 'success':
        problems.append('Claude reported an error: ' + str(result.get('result', result.get('errors', 'missing result'))))
    if result.get('session_id') != session or init.get('session_id') != session:
        problems.append('session ID mismatch')
    if init.get('cwd') and Path(init['cwd']).resolve() != checkout:
        problems.append('checkout mismatch in init')
    actual_mode = init.get('permissionMode')
    if ('manual' if actual_mode == 'default' else actual_mode) != mode:
        problems.append('permission mode mismatch')
    denials = result.get('permission_denials', [])
    if denials or any(e.get('type') == 'system' and e.get('subtype') == 'permission_denied' for e in events):
        problems.append('permission denied; inspect the artifacts before a scoped correction')
    servers = init.get('mcp_servers', [])
    if not isinstance(servers, list) or any(not isinstance(s, dict) or s.get('status') not in ('connected', 'ready') for s in servers):
        problems.append('an MCP server is not connected')
    return {'status': 'success' if not problems else 'failure', 'problems': problems,
            'session': {k: init.get(k) for k in ('session_id', 'cwd', 'model', 'permissionMode', 'tools', 'mcp_servers')},
            'result': result}


def compact_status(task_dir):
    """Read persisted metadata only; never parse the implementation stream."""
    task_path = checked(Path(task_dir).expanduser().absolute())
    task = task_path.resolve(strict=True)
    if not task.is_dir():
        raise Refusal('task path must be a directory')
    state = json.loads(checked(task / 'runner-state.json').read_text())
    if not isinstance(state, dict):
        raise Refusal('state must be a JSON object')
    if state.get('task_dir') != str(task):
        raise Refusal('task directory mismatch')
    number = state.get('round_count')
    if not isinstance(number, int) or number < 1:
        raise Refusal('invalid task round count')
    rounds = checked(task / 'rounds')
    folder = checked(rounds / f'{number:03d}')
    if not rounds.is_dir() or not folder.is_dir():
        raise Refusal('recorded task round is unavailable')
    checkpoint = checked(folder / 'checkpoint.md')
    summary = checked(folder / 'summary.json')
    return {'recorded_status': state.get('status'), 'round': number,
            'session_id': state.get('session_id'),
            'checkpoint': str(checkpoint) if checkpoint.is_file() else None,
            'checkpoint_modified_at': checkpoint.stat().st_mtime if checkpoint.is_file() else None,
            'summary': str(summary) if summary.is_file() else None,
            'note': 'Persisted status is not process liveness or write-ownership evidence.'}


def checkpoint_rule(checkpoint):
    # Do not interpolate glob syntax or rule separators into an allow rule.
    value = str(checkpoint)
    if any(character in value for character in '*?[]{}(),\\\n\r'):
        raise Refusal('checkpoint path cannot be represented as an exact permission rule')
    return f'Edit(/{value})'  # CLI absolute-path rules start with two slashes.


def command(args, binary, session, resume, task, checkpoint):
    result = [binary, '-p', '--output-format', 'stream-json', '--verbose',
              '--model', args.model, '--effort', args.effort,
              '--permission-mode', args.permission_mode, '--permission-prompts', 'none',
              '--max-turns', str(args.max_turns), '--max-budget-usd', str(args.max_budget_usd),
              '--resume' if resume else '--session-id', session,
              '--add-dir', str(task), '--allowedTools', checkpoint_rule(checkpoint)]
    for rule in args.allow_tool:
        result += ['--allowedTools', rule]
    if args.tools is not None:
        result += ['--tools', args.tools]
    for config in args.mcp_config:
        result += ['--mcp-config', config]
    if args.strict_mcp_config:
        result.append('--strict-mcp-config')
    return result


def checkpoint_metadata(path, now=None):
    """Metadata supports resumption review, never proof of meaningful progress."""
    checked(path)
    if not path.exists():
        return {'path': str(path), 'exists': False, 'progress_verified': False}
    if not path.is_file():
        raise Refusal('checkpoint must be a regular file')
    stat = path.stat()
    return {'path': str(path), 'exists': True, 'bytes': stat.st_size,
            'modified_at': stat.st_mtime,
            'age_seconds': max(0, (time.time() if now is None else now) - stat.st_mtime),
            'progress_verified': False}


def validate_limits(limits):
    if not isinstance(limits, dict):
        raise Refusal('saved limits must be an object')
    for name in DEFAULT_LIMITS:
        value = limits.get(name)
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value <= 0
                or (name in ('max_turns', 'max_rounds') and not isinstance(value, int))):
            raise Refusal('invalid or missing saved limit: ' + name)


def execution_plan(args, checkout, task):
    """Resolve limits without probing or starting Claude or writing task files."""
    state_path = checked(task / 'runner-state.json')
    state = json.loads(state_path.read_text()) if state_path.exists() else None
    if state_path.exists() and not isinstance(state, dict):
        raise Refusal('state must be a JSON object')
    previous = None
    inherited = None
    if state is not None:
        if state.get('version') != 1 or state.get('checkout') != str(checkout) or state.get('task_dir') != str(task):
            raise Refusal('state version, checkout or task directory mismatch')
        uuid.UUID(state['session_id'])
        number, maximum = state.get('round_count'), state.get('max_rounds')
        if (type(number) is not int or type(maximum) is not int
                or number < 1 or number >= maximum):
            raise Refusal('invalid or exhausted task round count')
        folder = checked(checked(task / 'rounds') / f'{number:03d}')
        if not folder.is_dir():
            raise Refusal('recorded task round is unavailable')
        summary_path = checked(folder / 'summary.json')
        summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
        if not isinstance(summary, dict):
            raise Refusal('previous summary must be an object')
        if summary and (summary.get('session_id') != state['session_id']
                        or summary.get('round') != number or summary.get('checkout') != str(checkout)):
            raise Refusal('previous summary identity mismatch')
        # Older runner states kept limits only in each round summary.
        inherited = state.get('limits', summary.get('limits'))
        validate_limits(inherited)
        if inherited['max_rounds'] != maximum:
            raise Refusal('saved maximum rounds mismatch')
        if args.max_rounds is not None and args.max_rounds != maximum:
            raise Refusal('the task maximum rounds is fixed at its first invocation')
        result, process = summary.get('result', {}), summary.get('process', {})
        if not isinstance(result, dict) or not isinstance(process, dict):
            raise Refusal('invalid previous result metadata')
        ended = summary.get('finished_at')
        if ended is not None and (isinstance(ended, bool) or not isinstance(ended, (int, float))
                                  or not math.isfinite(ended)):
            raise Refusal('invalid previous finish time')
        previous = {'round': number, 'recorded_status': state.get('status'),
                    'stop_reason': result.get('subtype') or process.get('status') or 'unknown',
                    'process_status': process.get('status'), 'limits': inherited,
                    'finished_at': ended,
                    'idle_seconds': max(0, time.time() - ended) if ended is not None else None,
                    'checkpoint': checkpoint_metadata(folder / 'checkpoint.md')}
    baseline = inherited if inherited is not None else DEFAULT_LIMITS
    limits = {name: getattr(args, name) if getattr(args, name) is not None else baseline[name]
              for name in DEFAULT_LIMITS}
    validate_limits(limits)
    fresh_reason = ('initial' if state is None else 'requested' if args.new_session else
                    'idle' if previous['idle_seconds'] is not None and previous['idle_seconds'] >= 3600
                    else None)
    report = {'resumed': state is not None and fresh_reason is None,
              'new_session_reason': fresh_reason, 'session_id': state.get('session_id') if state else None,
              'next_round': state['round_count'] + 1 if state else 1, 'limits': limits,
              'limit_sources': {name: 'explicit' if getattr(args, name) is not None
                                else ('previous_round' if state else 'protective_default')
                                for name in DEFAULT_LIMITS},
              'previous': previous,
              'note': 'CLI cost is not subscription quota; checkpoint metadata does not prove progress or write ownership.'}
    return state, report


def plan(args):
    checkout = Path(args.checkout).expanduser().resolve(strict=True)
    task = checked(Path(args.task_dir).expanduser().absolute()).resolve()
    if task == checkout or checkout in task.parents:
        raise Refusal('--task-dir must be outside the checkout')
    return execution_plan(args, checkout, task)[1]


def run(args):
    checkout = Path(args.checkout).expanduser().resolve(strict=True)
    if Path(git(checkout, 'rev-parse', '--show-toplevel').decode().strip()).resolve() != checkout:
        raise Refusal('--checkout must be the Git worktree root')
    task = checked(Path(args.task_dir).expanduser().absolute())
    if task.resolve() == checkout or checkout in task.resolve().parents:
        raise Refusal('--task-dir must be outside the checkout')
    task.mkdir(parents=True, exist_ok=True, mode=0o700)
    task = task.resolve()
    lock_path = Path(git(checkout, 'rev-parse', '--git-path', 'coordinate-codex-claude.lock').decode().strip())
    if not lock_path.is_absolute():
        lock_path = checkout / lock_path
    with locked(task / '.task.lock'), locked(lock_path):
        binary = executable(args.claude_bin)
        preflight = probe(binary, checkout)
        if not preflight['eligible']:
            raise Refusal('; '.join(preflight['problems']))
        state_path = checked(task / 'runner-state.json')
        state, planned = execution_plan(args, checkout, task)
        for name, value in planned['limits'].items():
            setattr(args, name, value)
        resume = planned['resumed']
        if state is None:
            state = {'version': 1, 'checkout': str(checkout), 'task_dir': str(task),
                     'session_id': str(uuid.uuid4()), 'round_count': 0, 'max_rounds': args.max_rounds}
        elif not resume:
            state['session_id'] = str(uuid.uuid4())
        request = Path(args.request_file).read_text()
        if len(request.encode()) > 512 * 1024:
            raise Refusal('request exceeds 512 KiB')
        rounds = checked(task / 'rounds')
        rounds.mkdir(mode=0o700, exist_ok=True)
        folder = checked(rounds / f"{state['round_count'] + 1:03d}")
        checkpoint = folder / 'checkpoint.md'
        checkpoint_rule(checkpoint)  # Validate before creating a round or starting Claude.
        folder.mkdir(mode=0o700)  # Never overwrite a previous attempt's evidence.
        prompt = (f'This explicitly invoked workflow is coordinated by Codex. You implement; Codex reviews.\n'
                  f'Use exactly this checkout: {checkout}\nDo not start background work, publish, or commit unless explicitly requested.\n'
                  'Stop all writes and verification before returning. Follow the bounded task request; do not retry denied actions.\n'
                  'Codex owns the private task record and captures the exact Git diff automatically.\n'
                  f'For private progress records, you own this separate checkpoint: {folder / "checkpoint.md"}\n'
                  'Use the Write tool to replace the checkpoint contents at milestones; no shell rename or acknowledgement is needed.\n\n'
                  + SKILL.read_text() + '\n\n# Current task request\n' + request)
        new_file(folder / 'prompt.md', prompt.encode())
        snapshot(checkout, folder, 'before')
        started_at = time.time()
        state.update(round_count=state['round_count'] + 1, status='running', limits=planned['limits'])
        atomic_json(state_path, state)  # Persist identity and count before spawning.
        summary = {'status': 'failure', 'round': state['round_count'], 'session_id': state['session_id'],
                   'started_at': started_at, 'execution_plan': planned,
                   'resumed': resume, 'checkout': str(checkout), 'artifacts': str(folder),
                   'checkpoint': str(checkpoint),
                   'scoped_access': {'additional_directory': str(task), 'checkpoint_edit_rule': checkpoint_rule(checkpoint)},
                   'probe': preflight, 'requested_model': args.model, 'requested_effort': args.effort,
                   'limits': {k: getattr(args, k) for k in ('timeout', 'max_turns', 'max_rounds', 'max_budget_usd')},
                   'notes': ['Cost figures are CLI estimates, not a subscription bill.',
                             'Success means implementation returned; Codex must still review the actual diff.']}
        try:
            process = execute(command(args, binary, state['session_id'], resume, task, checkpoint), checkout, folder, args.timeout)
            summary['process'] = process
            summary.update(evaluate(folder / 'stdout.jsonl', process, state['session_id'], checkout, args.permission_mode))
        except (OSError, ValueError, Refusal, subprocess.SubprocessError, KeyboardInterrupt) as error:
            summary['problems'] = [f'{type(error).__name__}: {error}']
        finally:
            try:
                snapshot(checkout, folder, 'after')
            except (OSError, Refusal, subprocess.SubprocessError) as error:
                summary['status'] = 'failure'
                summary.setdefault('problems', []).append('Git snapshot failed: ' + str(error))
            summary['finished_at'] = time.time()
            try:
                summary['checkpoint_metadata'] = checkpoint_metadata(checkpoint, summary['finished_at'])
            except (OSError, Refusal) as error:
                summary['status'] = 'failure'
                summary.setdefault('problems', []).append('Checkpoint metadata failed: ' + str(error))
            atomic_json(folder / 'summary.json', summary)
            state.update(status=summary['status'], last_summary=str(folder / 'summary.json'))
            atomic_json(state_path, state)
        return summary


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest='action', required=True)
    probe_parser = commands.add_parser('probe')
    probe_parser.add_argument('--claude-bin')
    probe_parser.add_argument('--checkout', default='.')
    probe_parser.add_argument('--timeout', type=positive, default=30)
    status_parser = commands.add_parser('status')
    status_parser.add_argument('--task-dir', required=True)
    r = commands.add_parser('run')
    r.add_argument('--claude-bin')
    for name in ('checkout', 'task-dir', 'request-file', 'effort'):
        r.add_argument('--' + name, required=True)
    r.add_argument('--model', default='opus',
                   help='Claude model alias (default: opus); pin a version only when explicitly requested')
    r.add_argument('--permission-mode', choices=('manual', 'auto'), default='manual')
    r.add_argument('--allow-tool', action='append', default=[])
    r.add_argument('--tools')
    r.add_argument('--mcp-config', action='append', default=[])
    r.add_argument('--strict-mcp-config', action='store_true')
    planning = commands.add_parser('plan', help='show effective limits and previous-round metadata without running Claude')
    planning.add_argument('--checkout', required=True)
    planning.add_argument('--task-dir', required=True)
    for target in (r, planning):
        target.add_argument('--new-session', action='store_true',
                            help='start fresh within the same task and round limits; use for new scope')
        for name in DEFAULT_LIMITS:
            target.add_argument('--' + name.replace('_', '-'),
                                type=count if name in ('max_turns', 'max_rounds') else positive,
                                default=None, help='inherit on resume; use protective defaults only for a new task')
    return p


def interrupt(_signum, _frame):
    raise KeyboardInterrupt()


def main():
    signal.signal(signal.SIGTERM, interrupt)
    args = parser().parse_args()
    try:
        if args.action == 'probe':
            result = probe(executable(args.claude_bin), Path(args.checkout).resolve(), args.timeout)
            success = result['eligible']
        elif args.action == 'plan':
            result = plan(args)
            success = True
        elif args.action == 'status':
            result = compact_status(args.task_dir)
            success = True
        else:
            result = run(args)
            success = result['status'] == 'success'
        print(json.dumps(result, ensure_ascii=False))
        return 0 if success else 1
    except (Refusal, OSError, ValueError, KeyError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        print(json.dumps({'status': 'refused', 'error': f'{type(error).__name__}: {error}'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
