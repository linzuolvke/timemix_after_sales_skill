import os
import unittest
import test_init_data as bootstrap

class ShallowDownload(unittest.TestCase):
    setUpClass = classmethod(bootstrap.BootstrapTests.setUpClass.__func__)
    setUp = bootstrap.BootstrapTests.setUp
    git = bootstrap.BootstrapTests.git
    fixture = bootstrap.BootstrapTests.fixture
    def test_latest_download_excludes_old_images_and_tags(self):
        repo = self.base / 'cases'
        image = repo / 'retired-image.bin'
        image.write_bytes(os.urandom(1024 * 1024))
        self.git(repo, 'add', '.')
        self.git(repo, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 'commit', '-qm', 'old screenshot')
        old_blob = self.git(repo, 'rev-parse', 'HEAD:retired-image.bin').strip()
        self.git(repo, 'tag', 'old-image-release')
        image.unlink()
        self.git(repo, 'add', '-u')
        self.git(repo, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 'commit', '-qm', 'text only')
        target = self.base / 'fresh'
        self.mod.clone_repo(repo.as_uri(), target)
        self.assertEqual(self.git(target, 'rev-parse', '--is-shallow-repository').strip(), 'true')
        self.assertEqual(self.git(target, 'rev-list', '--count', 'HEAD').strip(), '1')
        self.assertEqual(self.git(target, 'tag').strip(), '')
        self.assertFalse((target / image.name).exists())
        objects = self.git(target, 'rev-list', '--objects', '--all')
        self.assertNotIn(old_blob, objects)
        git_size = sum(p.stat().st_size for p in (target / '.git').rglob('*') if p.is_file())
        self.assertLess(git_size, 200000)
