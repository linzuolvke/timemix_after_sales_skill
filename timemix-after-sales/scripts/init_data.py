"""Initialize missing private datasets; preserve existing folders, then verify."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from check_data import DataError, default_root, identity, verify

REPOS = {
    'timemix_rules': 'https://github.com/linzuolvke/timemix_rules.git',
    'timemix_cases': 'https://github.com/linzuolvke/timemix_cases.git',
}

class InitError(Exception):
    pass


def git_environment():
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['GCM_INTERACTIVE'] = 'never'
    env['GIT_OPTIONAL_LOCKS'] = '0'
    return env


def clone_repo(url, destination):
    git = shutil.which('git')
    if not git:
        raise InitError('缺少Git；请由用户确认安装Git后重试')
    command = [git]
    gh = shutil.which('gh')
    if gh:
        auth = subprocess.run([gh, 'auth', 'status', '--hostname', 'github.com'],
                              capture_output=True, env=git_environment(), timeout=30)
        if auth.returncode == 0:
            # Use the authenticated CLI without copying credentials into files.
            command += ['-c', 'credential.helper=', '-c',
                        'credential.helper=!gh auth git-credential']
    command += ['clone', '--', url, str(destination)]
    try:
        result = subprocess.run(command, capture_output=True,
                                env=git_environment(), timeout=600)
    except subprocess.TimeoutExpired as exc:
        raise InitError('下载超时；暂存目录保留，请检查网络后重试') from exc
    if result.returncode:
        # Raw Git/credential-helper output may contain sensitive values.
        raise InitError('下载失败；请检查网络、GitHub登录及该私有库读取权限；不自动判定具体原因')


def modification_state(path):
    git = shutil.which('git')
    if not git or not (path / '.git').exists():
        return 'unknown'
    try:
        result = subprocess.run([git, '-C', str(path), 'status', '--porcelain'],
                                capture_output=True, env=git_environment(), timeout=30)
        return ('modified' if result.stdout else 'clean') if result.returncode == 0 else 'unknown'
    except (OSError, subprocess.TimeoutExpired):
        return 'unknown'


def initialize(root):
    root = Path(root).expanduser().resolve()
    missing = []
    for name in REPOS:
        target = root / name
        if os.path.lexists(target):
            try:
                identity(target, name[len('timemix_'):])
            except (DataError, OSError, ValueError, TypeError) as exc:
                raise InitError(f'已有目录身份或文件检查失败：{name}；保留原目录，不覆盖。{exc}') from exc
        else:
            missing.append(name)
    installed = []
    staging = None
    if missing:
        root.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix='.timemix-init-', dir=root))
    for name in missing:
        target = root / name
        download = staging / name
        try:
            clone_repo(REPOS[name], download)
            identity(download, name[len('timemix_'):])
            if os.path.lexists(target):
                raise InitError('下载期间目标目录已出现，停止以保护现有文件')
            download.rename(target)
            installed.append(name)
        except (InitError, DataError, OSError, ValueError, TypeError, subprocess.TimeoutExpired) as exc:
            done = '、'.join(installed) or '无'
            raise InitError(f'{name}初始化未完成：{exc}；已成功落盘的库：{done}（如有则保留）；暂存位置：{staging}') from exc
    if staging:
        staging.rmdir()
    try:
        result = verify(root)
    except (DataError, OSError, ValueError, TypeError, KeyError) as exc:
        raise InitError(f'完整资料校验失败，停止售后处理，保留本地资料：{exc}') from exc
    result['installed'] = installed
    result['local_modifications'] = {name: modification_state(root / name) for name in REPOS}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, help='Explicit local dataset root')
    args = parser.parse_args()
    try:
        root = args.root or (Path(os.environ['TIMEMIX_DATA_ROOT'])
                            if os.environ.get('TIMEMIX_DATA_ROOT') else default_root())
        result = initialize(root)
    except (InitError, DataError, OSError, ValueError, TypeError) as exc:
        print(json.dumps({'ok': False, 'reason': str(exc),
                          'action': '暂停售后处理；解决所述问题后重新初始化并校验'}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
