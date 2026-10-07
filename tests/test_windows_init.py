import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch
import test_init_data as bootstrap

class WindowsRegression(unittest.TestCase):
    setUpClass = classmethod(bootstrap.BootstrapTests.setUpClass.__func__)
    setUp = bootstrap.BootstrapTests.setUp
    git = bootstrap.BootstrapTests.git
    fixture = bootstrap.BootstrapTests.fixture

    def test_checkout_preserves_original_bytes_with_global_autocrlf(self):
        raw = self.base / 'cases/CASE_2026_001/records.md'
        raw.parent.mkdir(exist_ok=True)
        raw.write_bytes(b'original\nsecond line\n')
        import json
        manifest = self.base / 'cases/MANIFEST.json'
        value = json.loads(manifest.read_text())
        value['files'].append({'path':'CASE_2026_001/records.md','bytes':raw.stat().st_size,'sha256':hashlib.sha256(raw.read_bytes()).hexdigest()})
        manifest.write_text(json.dumps(value))
        self.git(self.base / 'cases','add','.')
        self.git(self.base / 'cases','-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','source')
        config = self.base / 'global-config'
        config.write_text('[core]\n autocrlf = true\n')
        with patch.dict(os.environ, {'GIT_CONFIG_GLOBAL':str(config)}):
            result = self.mod.initialize(self.root)
        self.assertTrue(result['ok'])
        self.assertEqual((self.root/'timemix_cases/CASE_2026_001/records.md').read_bytes(),raw.read_bytes())
        self.assertEqual(self.git(self.root/'timemix_cases','config','--local','core.autocrlf').strip(),'false')

    def test_selector_reset_before_manager(self):
        self.assertTrue(hasattr(self.mod,'git_command'), '缺少凭据助手选择入口')
        with patch.object(self.mod.sys, 'platform', 'win32'):
            with patch.object(self.mod.shutil,'which',side_effect=lambda name: '/git' if name == 'git' else None):
                with patch.object(self.mod,'run_bounded',side_effect=[subprocess.CompletedProcess([],0,b'helper-selector\n',b''),subprocess.CompletedProcess([],0,b'2.9',b'')]):
                    command=self.mod.git_command('https://github.com/linzuolvke/timemix_rules.git')
        self.assertLess(command.index('credential.helper='), command.index('credential.helper=manager'))

    def test_process_timeout_is_bounded(self):
        self.assertTrue(hasattr(self.mod,'run_bounded'), '缺少有进程树清理的限时执行工具')
        start=time.monotonic()
        with self.assertRaises(self.mod.CommandTimeout):
            self.mod.run_bounded([sys.executable,'-c','import time; time.sleep(5)'], timeout=0.15)
        self.assertLess(time.monotonic()-start,3)

    def test_preflight_emits_progress_before_clone(self):
        output=io.StringIO()
        with redirect_stderr(output):
            self.mod.initialize(self.root)
        self.assertIn('访问',output.getvalue())
        self.assertIn('下载',output.getvalue())

    def test_failed_access_never_starts_download(self):
        failure = subprocess.CompletedProcess([], 128, b'', b'Authentication failed SECRET')
        with patch.object(self.mod, 'git_command', return_value=['git']):
            with patch.object(self.mod, 'run_bounded', return_value=failure) as run:
                with self.assertRaises(self.mod.InitError) as error:
                    self.mod.clone_repo('https://github.com/linzuolvke/timemix_rules.git', self.base/'download')
        self.assertEqual(run.call_count, 1)
        self.assertEqual(error.exception.code, 'repository_access_failed')
        self.assertNotIn('SECRET', str(error.exception))

    def test_proxy_failure_not_reported_as_missing_permission(self):
        failure = subprocess.CompletedProcess([], 128, b'', b'CONNECT tunnel failed, response 502')
        error = self.mod.access_failure(failure)
        self.assertEqual(error.code, 'network_failed')

    def test_explicit_git_and_manager_only_change_this_command(self):
        command = self.mod.git_command('https://github.com/linzuolvke/timemix_rules.git', '/already installed/git', 'manager')
        self.assertEqual(command[0], '/already installed/git')
        self.assertIn('credential.helper=', command)
        self.assertIn('credential.helper=manager', command)
        self.assertIn('core.autocrlf=false', command)

    def test_explicit_git_is_used_for_modification_state(self):
        p = self.base / 'rules'
        completed = subprocess.CompletedProcess([], 0, b'', b'')
        with patch.object(self.mod, 'run_bounded', return_value=completed) as run:
            state = self.mod.modification_state(p, '/installed/git')
        self.assertEqual(state, 'clean')
        self.assertEqual(run.call_args.args[0][0], '/installed/git')

if __name__=='__main__':
    unittest.main(verbosity=2)
