#!/usr/bin/env python3
"""Exercise the external CLI contract without real model calls or credentials."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/claude_runner.py'
spec = importlib.util.spec_from_file_location('runner', SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

FAKE = '''#!/usr/bin/env python3
import json,os,sys,subprocess,time,signal
from pathlib import Path
args=sys.argv[1:]
def value(flag): return args[args.index(flag)+1]
if args==['--version']:
    print('2.1.275 (Claude Code)');sys.exit(0)
if args==['--help']:
    print('--print --output-format --verbose --model --effort --max-budget-usd --permission-mode --permission-prompts --session-id --resume --allowedTools --tools --mcp-config --strict-mcp-config --add-dir');sys.exit(0)
if args==['auth','status','--json']:
    Path('auth-cwd.txt').write_text(os.getcwd())
    print(json.dumps(dict(loggedIn=True,authMethod='claude.ai',apiProvider='firstParty',subscriptionType='pro',email='must-not-appear@example.com',token='must-not-appear')));sys.exit(0)
mode=Path('scenario.txt').read_text() if Path('scenario.txt').exists() else 'ok'
with open('invocations.jsonl','a') as f:f.write(json.dumps(args)+'\\n')
assert '--allow-tool' not in args
assert '--continue' not in args
assert '--permission-prompts' in args and value('--permission-prompts')=='none'
assert '--max-turns' in args and '--max-budget-usd' in args
session=value('--resume') if '--resume' in args else value('--session-id')
Path('received-prompt.txt').write_text(sys.stdin.read())
init=dict(type='system',subtype='init',session_id=session,cwd=os.getcwd(),model='test-model',permissionMode='default',tools=['Read'],mcp_servers=[])
if mode=='wrong-mode':init['permissionMode']='bypassPermissions'
if mode=='bad-mcp':init['mcp_servers']=[dict(name='required',status='failed')]
print(json.dumps(init),flush=True)
if mode in ('timeout','interrupt'):
    Path('running').write_text('yes')
    if mode=='timeout':
        child="import signal,time;from pathlib import Path;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(4);Path('survived').write_text('bad');time.sleep(10)"
        subprocess.Popen([sys.executable,'-c',child])
    time.sleep(30)
if mode=='missing':sys.exit(0)
if mode=='malformed':print('not JSON')
if mode=='denied':print(json.dumps(dict(type='system',subtype='permission_denied',tool_name='Edit')))
result=dict(type='result',subtype='success',is_error=False,session_id=session,result='implemented',permission_denials=[],total_cost_usd=0.01)
if mode=='error':result.update(is_error=True,result="You've hit your session limit")
if mode=='wrong-session':result['session_id']='wrong-session'
if mode=='result-denied':result['permission_denials']=[dict(tool_name='Edit')]
print(json.dumps(result))
if mode=='duplicate':print(json.dumps(result))
'''


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.task = self.root / 'task'
        self.request = self.root / 'request.md'
        self.request.write_text('Implement the bounded test task.')
        self.fake = self.root / 'fake-claude'
        self.fake.write_text(FAKE)
        self.fake.chmod(0o700)
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        (self.repo / 'code.txt').write_text('baseline\n')
        subprocess.run(['git', 'add', '.'], cwd=self.repo, check=True)
        subprocess.run(['git', '-c', 'user.name=Test', '-c', 'user.email=test@localhost',
                        'commit', '-qm', 'Add fixture'], cwd=self.repo, check=True)
        self.env = dict(os.environ)
        for name in runner.AUTH_ENV:
            self.env.pop(name, None)
        self.env['PYTHONDONTWRITEBYTECODE'] = '1'

    def tearDown(self):
        self.temp.cleanup()

    def args(self, *extra):
        return [sys.executable, str(SCRIPT), 'run', '--claude-bin', str(self.fake),
                '--checkout', str(self.repo), '--task-dir', str(self.task),
                '--request-file', str(self.request), '--model', 'test-model',
                '--effort', 'high', '--timeout', '10', *extra]

    def invoke(self, scenario='ok', *extra):
        (self.repo / 'scenario.txt').write_text(scenario)
        p = subprocess.run(self.args(*extra), cwd=self.root, env=self.env,
                           capture_output=True, text=True, timeout=30)
        return p, json.loads(p.stdout)

    def test_round_trip_uses_exact_session_and_scoped_flags(self):
        first, a = self.invoke('ok', '--allow-tool', 'Edit', '--tools', '')
        second, b = self.invoke()
        self.assertEqual(first.returncode, 0, a)
        self.assertEqual(second.returncode, 0, b)
        self.assertEqual(a['session_id'], b['session_id'])
        self.assertFalse(a['resumed'])
        self.assertTrue(b['resumed'])
        calls = [json.loads(line) for line in (self.repo / 'invocations.jsonl').read_text().splitlines()]
        self.assertIn('--allowedTools', calls[0])
        for number, call in enumerate(calls, 1):
            self.assertEqual(call[call.index('--add-dir') + 1], str(self.task))
            rule = runner.checkpoint_rule(self.task / f'rounds/{number:03d}/checkpoint.md')
            self.assertIn(rule, call)
            self.assertNotIn('Write', call)
        self.assertNotEqual(calls[0][calls[0].index('--allowedTools') + 1],
                            calls[1][calls[1].index('--allowedTools') + 1])
        self.assertIn('--session-id', calls[0])
        self.assertIn('--resume', calls[1])
        self.assertEqual((self.repo / 'auth-cwd.txt').read_text(), str(self.repo))
        self.assertIn('This explicitly invoked workflow', (self.repo / 'received-prompt.txt').read_text())
        self.assertNotIn('must-not-appear', first.stdout)
        before = json.loads((self.task / 'rounds/001/git-before.json').read_text())
        self.assertIn('sha256', before['unstaged'])

    def test_fresh_sessions_preserve_task_rounds_and_limits(self):
        _, first = self.invoke('ok', '--max-rounds', '3', '--max-turns', '75')
        _, second = self.invoke('ok', '--new-session')
        self.assertFalse(second['resumed'])
        self.assertNotEqual(first['session_id'], second['session_id'])
        self.assertEqual(second['round'], 2)
        self.assertEqual(second['limits'], first['limits'])
        self.assertTrue((self.task / 'rounds/001/summary.json').is_file())
        _, third = self.invoke()
        self.assertTrue(third['resumed'])
        self.assertEqual(second['session_id'], third['session_id'])
        refused, result = self.invoke('ok', '--new-session')
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('exhausted', result['error'])

    def test_idle_selection_uses_finish_not_start(self):
        _, first = self.invoke()
        path = self.task / 'rounds/001/summary.json'
        summary = json.loads(path.read_text())
        summary['started_at'] = 1
        summary['finished_at'] = 10000
        path.write_text(json.dumps(summary))
        args = runner.parser().parse_args(['plan', '--checkout', str(self.repo),
                                         '--task-dir', str(self.task)])
        for now, resumed in ((10001, True), (13599, True), (13600, False)):
            with patch.object(runner.time, 'time', return_value=now):
                plan = runner.plan(args)
            self.assertEqual(plan['resumed'], resumed)
        _, second = self.invoke()
        self.assertFalse(second['resumed'])
        self.assertEqual(second['execution_plan']['new_session_reason'], 'idle')
        self.assertNotEqual(first['session_id'], second['session_id'])
        call = json.loads((self.repo / 'invocations.jsonl').read_text().splitlines()[-1])
        self.assertIn('--session-id', call)
        self.assertNotIn('--resume', call)

    def test_batch_counts_items_and_followup_independently(self):
        _, first = self.invoke('ok', '--work-item', 'a', '--work-item', 'b', '--work-item', 'c')
        self.assertEqual(first['limits']['max_rounds'], 3)
        self.assertEqual(first['execution_plan']['item_rounds_after_launch'], {'a': 1, 'b': 1, 'c': 1})
        for item in ('a', 'b', 'c'):
            for attempt in (2, 3):
                process, result = self.invoke('ok', '--work-item', item)
                self.assertEqual(process.returncode, 0, result)
                self.assertEqual(result['execution_plan']['item_rounds_after_launch'][item], attempt)
        refused, result = self.invoke('ok', '--work-item', 'a', '--new-session')
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('exhausted', result['error'])
        process, followup = self.invoke('ok', '--work-item', 'a-followup-1', '--new-session')
        self.assertEqual(process.returncode, 0, followup)
        self.assertEqual(followup['execution_plan']['item_rounds_after_launch'],
                         {'a': 3, 'b': 3, 'c': 3, 'a-followup-1': 1})
        self.assertEqual(followup['round'], 8)
        self.assertFalse(followup['resumed'])

    def test_legacy_counts_and_invalid_item_ledger(self):
        self.invoke('ok', '--max-rounds', '4')
        path = self.task / 'runner-state.json'
        state = json.loads(path.read_text())
        for counts in ({}, {'default': 0}, {'default': True}):
            state['item_rounds'] = counts
            path.write_text(json.dumps(state))
            self.assertNotEqual(self.invoke()[0].returncode, 0)
        state.pop('item_rounds')
        state.pop('work_items')
        path.write_text(json.dumps(state))
        self.assertNotEqual(self.invoke('ok', '--work-item', 'a')[0].returncode, 0)
        process, resumed = self.invoke()
        self.assertEqual(process.returncode, 0, resumed)
        self.assertEqual(resumed['limits']['max_rounds'], 4)
        self.assertEqual(resumed['execution_plan']['item_rounds_after_launch'], {'default': 2})

    def test_duplicate_work_items_do_not_launch(self):
        process, result = self.invoke('ok', '--work-item', 'a', '--work-item', 'a')
        self.assertNotEqual(process.returncode, 0)
        self.assertFalse((self.repo / 'invocations.jsonl').exists())

    def test_default_alias_and_explicit_model_reach_cli(self):
        args = self.args('--effort', 'xhigh')
        index = args.index('--model')
        del args[index:index + 2]
        for extra, expected in (([], 'opus'), (['--model', 'pinned-test-model'], 'pinned-test-model')):
            process = subprocess.run(args + extra, cwd=self.root, env=self.env,
                                     capture_output=True, text=True, timeout=30)
            summary = json.loads(process.stdout)
            self.assertEqual(process.returncode, 0, summary)
            call = json.loads((self.repo / 'invocations.jsonl').read_text().splitlines()[-1])
            self.assertEqual(call[call.index('--model') + 1], expected)
            self.assertEqual(call[call.index('--effort') + 1], 'xhigh')
            self.assertEqual(summary['requested_model'], expected)
            self.assertEqual(summary['session']['model'], 'test-model')

    def test_resume_inherits_limits_and_honors_explicit_overrides(self):
        first, a = self.invoke('ok', '--timeout', '123', '--max-turns', '75',
                               '--max-budget-usd', '12', '--max-rounds', '3')
        self.assertEqual(first.returncode, 0, a)
        args = self.args()
        index = args.index('--timeout')
        del args[index:index + 2]
        second = subprocess.run(args, env=self.env, capture_output=True, text=True, timeout=30)
        b = json.loads(second.stdout)
        self.assertEqual(second.returncode, 0, b)
        self.assertEqual(b['limits'], a['limits'])
        self.assertEqual(set(b['execution_plan']['limit_sources'].values()), {'previous_round'})
        self.assertEqual(b['execution_plan']['previous']['stop_reason'], 'success')
        self.assertIsNotNone(b['execution_plan']['previous']['idle_seconds'])
        calls = [json.loads(line) for line in (self.repo / 'invocations.jsonl').read_text().splitlines()]
        self.assertEqual(calls[1][calls[1].index('--max-turns') + 1], '75')
        self.assertEqual(float(calls[1][calls[1].index('--max-budget-usd') + 1]), 12)
        third, c = self.invoke('ok', '--max-budget-usd', '5')
        self.assertEqual(third.returncode, 0, c)
        self.assertEqual(c['limits']['max_budget_usd'], 5)
        self.assertEqual(c['limits']['max_turns'], 75)
        self.assertEqual(c['execution_plan']['limit_sources']['max_budget_usd'], 'explicit')

    def test_plan_is_read_only_and_reports_checkpoint_without_its_contents(self):
        def inspect():
            process = subprocess.run([sys.executable, str(SCRIPT), 'plan',
                '--checkout', str(self.repo), '--task-dir', str(self.task)],
                env=self.env, capture_output=True, text=True, timeout=10)
            self.assertEqual(process.returncode, 0, process.stdout)
            return json.loads(process.stdout)
        initial = inspect()
        self.assertFalse(self.task.exists())
        self.assertFalse((self.repo / 'invocations.jsonl').exists())
        self.assertEqual(initial['limits'], runner.DEFAULT_LIMITS)
        self.invoke('ok', '--max-budget-usd', '11')
        checkpoint = self.task / 'rounds/001/checkpoint.md'
        checkpoint.write_text('private checkpoint contents must not appear')
        before = {p: p.read_bytes() for p in self.task.rglob('*') if p.is_file()}
        calls = (self.repo / 'invocations.jsonl').read_bytes()
        resumed = inspect()
        self.assertEqual(resumed['limits']['max_budget_usd'], 11)
        self.assertGreater(resumed['previous']['checkpoint']['bytes'], 0)
        self.assertFalse(resumed['previous']['checkpoint']['progress_verified'])
        self.assertNotIn('private checkpoint contents', json.dumps(resumed))
        self.assertEqual(before, {p: p.read_bytes() for p in self.task.rglob('*') if p.is_file()})
        self.assertEqual(calls, (self.repo / 'invocations.jsonl').read_bytes())

    def test_legacy_resume_uses_summary_limits_and_unknown_finish_time(self):
        self.invoke('ok', '--max-budget-usd', '9')
        state_path = self.task / 'runner-state.json'
        state = json.loads(state_path.read_text())
        state.pop('limits')
        state_path.write_text(json.dumps(state))
        summary_path = self.task / 'rounds/001/summary.json'
        summary = json.loads(summary_path.read_text())
        summary.pop('finished_at')
        summary_path.write_text(json.dumps(summary))
        p, data = self.invoke()
        self.assertEqual(p.returncode, 0, data)
        self.assertEqual(data['limits']['max_budget_usd'], 9)
        self.assertIsNone(data['execution_plan']['previous']['idle_seconds'])

    def test_bad_saved_limits_and_summary_identity_refuse_without_launch(self):
        for scenario in ('missing', 'boolean', 'identity', 'linked-summary', 'null-state'):
            with self.subTest(scenario=scenario):
                self.task = self.root / scenario
                self.invoke()
                state_path = self.task / 'runner-state.json'
                state = json.loads(state_path.read_text())
                summary_path = self.task / 'rounds/001/summary.json'
                summary = json.loads(summary_path.read_text())
                if scenario == 'missing':
                    state.pop('limits')
                    summary.pop('limits')
                elif scenario == 'boolean':
                    state['limits']['max_turns'] = True
                elif scenario == 'identity':
                    summary['session_id'] = 'other-session'
                if scenario == 'linked-summary':
                    saved = self.root / 'external-summary.json'
                    saved.write_text(json.dumps(summary))
                    summary_path.unlink()
                    summary_path.symlink_to(saved)
                else:
                    summary_path.write_text(json.dumps(summary))
                state_path.write_text('null' if scenario == 'null-state' else json.dumps(state))
                before = (self.repo / 'invocations.jsonl').read_bytes()
                p, data = self.invoke()
                self.assertNotEqual(p.returncode, 0, data)
                self.assertEqual(before, (self.repo / 'invocations.jsonl').read_bytes())
                self.assertFalse((self.task / 'rounds/002').exists())

    def test_zero_exit_is_not_enough(self):
        for scenario in ('missing', 'malformed', 'duplicate', 'error', 'denied',
                         'result-denied', 'bad-mcp', 'wrong-session', 'wrong-mode'):
            with self.subTest(scenario=scenario):
                self.task = self.root / scenario
                p, data = self.invoke(scenario)
                self.assertNotEqual(p.returncode, 0)
                self.assertEqual(data['status'], 'failure')
                state = json.loads((self.task / 'runner-state.json').read_text())
                self.assertEqual(state['status'], 'failure')
                self.assertEqual(state['round_count'], 1)

    def test_round_limit_counts_failed_attempts(self):
        self.invoke('error', '--max-rounds', '1')
        p, data = self.invoke('ok', '--max-rounds', '1')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('exhausted', data['error'])
        self.assertEqual(len((self.repo / 'invocations.jsonl').read_text().splitlines()), 1)

    def test_checkout_mismatch_refused(self):
        self.invoke()
        state = self.task / 'runner-state.json'
        data = json.loads(state.read_text())
        data['checkout'] = str(self.root)
        state.write_text(json.dumps(data))
        p, data = self.invoke()
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('mismatch', data['error'])

    def test_linked_state_and_rounds_refused(self):
        self.task.mkdir()
        target = self.root / 'preserve.json'
        target.write_text('do not overwrite')
        state = self.task / 'runner-state.json'
        state.symlink_to(target)
        p, data = self.invoke()
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(target.read_text(), 'do not overwrite')
        state.unlink()
        (self.task / 'rounds').symlink_to(self.root)
        p, data = self.invoke()
        self.assertNotEqual(p.returncode, 0)

    def test_task_inside_checkout_and_task_symlink_refused(self):
        self.task = self.repo / 'private'
        self.assertNotEqual(self.invoke()[0].returncode, 0)
        self.task = self.root / 'linked-task'
        self.task.symlink_to(self.repo, target_is_directory=True)
        self.assertNotEqual(self.invoke()[0].returncode, 0)

    def test_locks_cover_task_and_checkout(self):
        self.task.mkdir()
        for path in (self.task / '.task.lock', self.repo / '.git/coordinate-codex-claude.lock'):
            with runner.locked(path):
                p, data = self.invoke()
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('another runner', data['error'])

    def test_timeout_kills_child_that_outlives_parent(self):
        p, data = self.invoke('timeout', '--timeout', '0.8')
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(data['process']['status'], 'timeout')
        time.sleep(2)
        self.assertFalse((self.repo / 'survived').exists())
        self.assertEqual(json.loads((self.task / 'runner-state.json').read_text())['round_count'], 1)

    def test_interrupt_preserves_session_and_releases_locks(self):
        (self.repo / 'scenario.txt').write_text('interrupt')
        p = subprocess.Popen(self.args(), cwd=self.root, env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 10
            while not (self.repo / 'running').exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertTrue((self.repo / 'running').exists())
            initial = json.loads((self.task / 'runner-state.json').read_text())
            self.assertEqual(initial['status'], 'running')
            p.send_signal(signal.SIGINT)
            stdout, _ = p.communicate(timeout=10)
            interrupted = json.loads(stdout)
            self.assertEqual(interrupted['process']['status'], 'interrupted')
            _, resumed = self.invoke()
            self.assertEqual(resumed['session_id'], initial['session_id'])
            self.assertTrue(resumed['resumed'])
        finally:
            if p.poll() is None:
                p.kill()
                p.wait()

    def test_alternate_credentials_refused_without_exposure(self):
        self.env['ANTHROPIC_API_KEY'] = 'must-not-appear-secret'
        p, data = self.invoke()
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn('must-not-appear-secret', p.stdout + p.stderr)
        self.assertFalse((self.repo / 'invocations.jsonl').exists())

    def test_official_endpoints_keep_subscription_route(self):
        for name in runner.ENDPOINT_ENV:
            self.env[name] = runner.OFFICIAL_ENDPOINT
        p, data = self.invoke()
        self.assertEqual(p.returncode, 0, data)
        self.env['ANTHROPIC_API_KEY'] = 'must-not-appear-secret'
        p, data = self.invoke()
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn('must-not-appear-secret', p.stdout)

    def test_endpoint_lookalikes_refused_before_probe(self):
        for name in runner.ENDPOINT_ENV:
            for value in ('https://api.anthropic.com/', 'http://api.anthropic.com',
                          'https://api.anthropic.com.evil.invalid',
                          'https://api.anthropic.com@evil.invalid',
                          'https://api.anthropic.com?secret=must-not-appear'):
                with self.subTest(name=name, value=value):
                    environment = {name: value}
                    with patch.dict(runner.os.environ, environment, clear=True), \
                            patch.object(runner, 'capture', side_effect=AssertionError('must not launch')):
                        result = runner.probe(str(self.fake), self.repo)
                    self.assertFalse(result['eligible'])
                    self.assertNotIn(value, json.dumps(result))

    def test_checkpoint_permission_rejects_pattern_injection(self):
        for part in ('bad*', 'bad?', 'bad[0]', 'bad,Write', 'bad)'):
            with self.subTest(part=part), self.assertRaises(runner.Refusal):
                runner.checkpoint_rule(self.root / part / 'checkpoint.md')
        self.assertEqual(runner.checkpoint_rule(Path('/private/tmp/task space/checkpoint.md')),
                         'Edit(//private/tmp/task space/checkpoint.md)')

    def test_invalid_limits_and_bypass_rejected(self):
        for flag, value in (('--timeout', 'nan'), ('--max-rounds', '0'),
                            ('--max-budget-usd', 'inf'), ('--max-turns', '-1'),
                            ('--permission-mode', 'bypassPermissions')):
            p = subprocess.run(self.args(flag, value), capture_output=True, env=self.env, timeout=10)
            self.assertNotEqual(p.returncode, 0)
        self.assertFalse((self.repo / 'invocations.jsonl').exists())

    def test_desktop_version_order_is_numeric(self):
        root = self.root / 'desktop'
        for version in ('2.1.9', '2.1.10'):
            p = root / version / 'claude.app/Contents/MacOS/claude'
            p.parent.mkdir(parents=True)
            p.write_text('binary')
            p.chmod(0o700)
        with patch.object(runner.shutil, 'which', return_value=None):
            self.assertIn('2.1.10/', runner.executable(desktop_root=root))


if __name__ == '__main__':
    unittest.main()
