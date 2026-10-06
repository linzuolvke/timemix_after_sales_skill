from pathlib import Path
import re
import unittest

REPO = Path(__file__).resolve().parents[1]
URLS = ('https://github.com/linzuolvke/timemix_rules', 'https://github.com/linzuolvke/timemix_cases')

class InstallContract(unittest.TestCase):
    def test_repo_entrypoint_has_addresses_and_skill_path(self):
        text = (REPO / 'README.md').read_text()
        for url in URLS:
            self.assertIn(url, text, '只读仓库首页应能找到两个依赖地址')
        self.assertIn('timemix-after-sales/SKILL.md', text)

    def test_discovery_description_includes_initialization(self):
        text = (REPO / 'timemix-after-sales/SKILL.md').read_text()
        description = re.search(r'^description: (.+)$', text, re.M).group(1)
        self.assertIn('初始化', description)
        self.assertIn('安装', description)

    def test_skill_start_has_repository_addresses(self):
        text = (REPO / 'timemix-after-sales/SKILL.md').read_text()
        header = text.split('## 首次初始化与本机资料检查')[0]
        for url in URLS:
            self.assertIn(url, header, '依赖地址应在Skill开头直接可见')

    def test_readme_requires_installed_package_verification(self):
        text = (REPO / 'README.md').read_text()
        for token in ('scripts/init_data.py', 'scripts/check_data.py', 'references/data-contract.md', '实际安装', '旧版'):
            self.assertIn(token, text)

if __name__ == '__main__':
    unittest.main(verbosity=2)
