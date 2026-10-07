import hashlib
import json
import unittest
import test_init_data as bootstrap

class CasesV2(unittest.TestCase):
    setUpClass = classmethod(bootstrap.BootstrapTests.setUpClass.__func__)
    setUp = bootstrap.BootstrapTests.setUp
    fixture = bootstrap.BootstrapTests.fixture
    git = bootstrap.BootstrapTests.git

    def refresh(self):
        repo = self.root / 'timemix_cases'
        manifest = repo / 'MANIFEST.json'
        value = json.loads(manifest.read_text())
        value['files'] = []
        for path in sorted(repo.glob('CASE_*/*.md')):
            raw = path.read_bytes()
            value['files'].append({'path':str(path.relative_to(repo)), 'bytes':len(raw),
                'sha256':hashlib.sha256(raw).hexdigest()})
        manifest.write_text(json.dumps(value))

    def test_old_schema_rejected(self):
        self.mod.initialize(self.root)
        path = self.root / 'timemix_cases/DATASET.json'
        value = json.loads(path.read_text())
        value['schema_version'] = 1
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(self.mod.InitError, '格式不符'):
            self.mod.initialize(self.root)

    def test_optional_records_and_discretion(self):
        self.mod.initialize(self.root)
        path = self.root / 'timemix_cases/CASE_2026_001/case.md'
        text = path.read_text().replace('status: closed', 'discretion: granted\nowner_judgment: "长期支持门店"\nstatus: closed')
        path.write_text(text)
        self.refresh()
        self.assertTrue(self.mod.initialize(self.root)['ok'])
        path.write_text(text.replace('granted', 'maybe'))
        self.refresh()
        with self.assertRaisesRegex(self.mod.InitError, '破例字段错误'):
            self.mod.initialize(self.root)

    def test_owner_judgment_requires_discretion(self):
        self.mod.initialize(self.root)
        path = self.root / 'timemix_cases/CASE_2026_001/case.md'
        path.write_text(path.read_text().replace('status: closed', 'owner_judgment: "要求较多"\nstatus: closed'))
        self.refresh()
        with self.assertRaisesRegex(self.mod.InitError, '缺少破例决定'):
            self.mod.initialize(self.root)

    def test_old_chat_folder_rejected(self):
        self.mod.initialize(self.root)
        (self.root / 'timemix_cases/chats').mkdir()
        with self.assertRaisesRegex(self.mod.InitError, '旧目录'):
            self.mod.initialize(self.root)

    def test_ai_discussion_in_records_rejected(self):
        self.mod.initialize(self.root)
        record = self.root / 'timemix_cases/CASE_2026_001/records.md'
        record.write_text('## ChatGPT\n建议给客户退款')
        self.refresh()
        with self.assertRaisesRegex(self.mod.InitError, '混入AI讨论'):
            self.mod.initialize(self.root)

    def test_unlisted_record_rejected(self):
        self.mod.initialize(self.root)
        record = self.root / 'timemix_cases/CASE_2026_001/records.md'
        record.write_text('2026-01-01 客户：你好')
        with self.assertRaisesRegex(self.mod.InitError, '完整性清单不一致'):
            self.mod.initialize(self.root)

if __name__ == '__main__':
    unittest.main()
