import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'timemix-after-sales/scripts'
sys.path.insert(0, str(SCRIPTS))

class BootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.available = (SCRIPTS / 'init_data.py').exists()
        if cls.available:
            import init_data
            cls.mod = init_data

    def setUp(self):
        self.assertTrue(self.available, '缺少自动初始化工具 init_data.py')
        self.tmp = tempfile.TemporaryDirectory(prefix='timemix-test-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / '资料 含空格'
        self.repos = {}
        for kind in ('rules', 'cases'):
            p = self.base / kind
            p.mkdir()
            self.fixture(p, kind)
            self.git(p, 'init', '-q')
            self.git(p, 'add', '.')
            self.git(p, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-qm', 'fixture')
            self.repos['timemix_' + kind] = str(p)
        self.addCleanup(patch.stopall)
        patch.object(self.mod, 'REPOS', self.repos).start()

    def git(self, root, *args):
        return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True, text=True).stdout

    def fixture(self, p, kind):
        def put(name, value):
            q = p / name
            q.parent.mkdir(parents=True, exist_ok=True)
            q.write_text(json.dumps(value) if isinstance(value, dict) else value, encoding='utf-8')
        put('DATASET.json', {'dataset': 'timemix_' + kind, 'schema_version': 1, 'version': 'v0.1.1', 'required_files': ['INDEX.md']})
        if kind == 'rules':
            put('INDEX.md', '[rule](current/test.md)')
            put('current/test.md', '---\nid: RULE_TEST_001\nstatus: active\n---\nTest')
        else:
            put('INDEX.md', '[case](cases/CASE_2026_001.md)')
            put('MANIFEST.json', {'version': 'v0.1.1', 'case_ids': ['CASE_2026_001'], 'case_count': 1})
            put('raw_manifest.json', {'files': []})
            put('cases/CASE_2026_001.md', '---\ncase_id: CASE_2026_001\nstatus: closed\nreview_status: approved\n---\nTest')

    def test_download_both_and_verify(self):
        result = self.mod.initialize(self.root)
        self.assertTrue(result['ok'])
        self.assertEqual(set(result['installed']), set(self.repos))
        self.assertTrue((self.root / 'timemix_cases/.git').is_dir())

    def test_existing_modified_files_preserved_and_no_network(self):
        self.mod.initialize(self.root)
        p = self.root / 'timemix_rules/current/test.md'
        p.write_text(p.read_text() + '\n本地修改', encoding='utf-8')
        with patch.object(self.mod, 'clone_repo', side_effect=AssertionError('不应下载')):
            result = self.mod.initialize(self.root)
        self.assertTrue(result['ok'])
        self.assertEqual(result['installed'], [])
        self.assertIn('本地修改', p.read_text())

    def test_only_missing_repo_downloaded(self):
        self.root.mkdir()
        shutil.copytree(self.base / 'rules', self.root / 'timemix_rules')
        result = self.mod.initialize(self.root)
        self.assertEqual(result['installed'], ['timemix_cases'])

    def test_existing_invalid_directory_not_overwritten(self):
        p = self.root / 'timemix_rules'
        p.mkdir(parents=True)
        (p / 'keep.txt').write_text('keep')
        with self.assertRaises(self.mod.InitError):
            self.mod.initialize(self.root)
        self.assertEqual((p / 'keep.txt').read_text(), 'keep')
        self.assertFalse((self.root / 'timemix_cases').exists())

    def test_failed_clone_reports_and_does_not_install_target(self):
        self.repos['timemix_rules'] = str(self.base / 'nonexistent')
        with self.assertRaises(self.mod.InitError):
            self.mod.initialize(self.root)
        self.assertFalse((self.root / 'timemix_rules').exists())

    def test_wrong_download_identity_rejected(self):
        self.repos['timemix_rules'] = str(self.base / 'cases')
        with self.assertRaises(self.mod.InitError):
            self.mod.initialize(self.root)
        self.assertFalse((self.root / 'timemix_rules').exists())

    def test_corrupt_existing_case_fails_offline(self):
        self.mod.initialize(self.root)
        p = self.root / 'timemix_cases/cases/CASE_2026_001.md'
        p.write_text(p.read_text().replace('approved', 'invented'))
        with patch.object(self.mod, 'clone_repo', side_effect=AssertionError('不应下载')):
            with self.assertRaises(self.mod.InitError):
                self.mod.initialize(self.root)
        self.assertIn('invented', p.read_text())

    def test_partial_first_clone_kept_if_second_fails(self):
        self.repos['timemix_cases'] = str(self.base / 'nonexistent')
        with self.assertRaises(self.mod.InitError):
            self.mod.initialize(self.root)
        self.assertTrue((self.root / 'timemix_rules/DATASET.json').exists())
        self.assertFalse((self.root / 'timemix_cases').exists())

    def test_clone_failure_does_not_expose_helper_output(self):
        fake = subprocess.CompletedProcess(['git'], 1, b'SECRET_OUTPUT', b'SECRET_ERROR')
        with patch.object(self.mod.shutil, 'which', side_effect=lambda name: '/usr/bin/git' if name == 'git' else None):
            with patch.object(self.mod.subprocess, 'run', return_value=fake) as run:
                with self.assertRaises(self.mod.InitError) as error:
                    self.mod.clone_repo('https://example.invalid/private.git', self.base / 'download')
        self.assertNotIn('SECRET', str(error.exception))
        env = run.call_args.kwargs['env']
        self.assertEqual(env['GIT_TERMINAL_PROMPT'], '0')
        self.assertEqual(env['GCM_INTERACTIVE'], 'never')

    def test_missing_git_is_explicit(self):
        with patch.object(self.mod.shutil, 'which', return_value=None):
            with self.assertRaisesRegex(self.mod.InitError, '缺少Git'):
                self.mod.clone_repo('https://example.invalid/private.git', self.base / 'download')

if __name__ == '__main__':
    unittest.main(verbosity=2)
