"""Initialize missing private datasets; preserve existing folders, then verify."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile

from check_data import DataError, default_root, identity, verify

REPOS = {
    'timemix_rules': 'https://github.com/linzuolvke/timemix_rules.git',
    'timemix_cases': 'https://github.com/linzuolvke/timemix_cases.git',
}

class InitError(Exception):
    def __init__(self, message, code='initialization_failed'):
        super().__init__(message)
        self.code = code

class CommandTimeout(Exception):
    pass


def git_environment():
    env = os.environ.copy()
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['GCM_INTERACTIVE'] = 'never'
    env['GIT_OPTIONAL_LOCKS'] = '0'
    return env


def run_bounded(command, timeout):
    options = {'start_new_session': True} if sys.platform != 'win32' else {
        'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               stdin=subprocess.DEVNULL, env=git_environment(), **options)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        # Only terminate the tree started by this invocation, never other Git jobs.
        if sys.platform == 'win32':
            try:
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               capture_output=True, timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                pass
            if process.poll() is None:
                process.kill()
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        raise CommandTimeout(f'操作超过{timeout}秒；已尝试终止本次启动的进程树') from exc
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def progress(message):
    print(message, file=sys.stderr, flush=True)


def git_command(url, git_executable=None, credential_helper=None):
    git = str(git_executable) if git_executable else shutil.which('git')
    if not git:
        raise InitError('缺少Git；请由用户确认安装Git后重试', 'missing_git')
    command = [git, '-c', 'core.autocrlf=false', '-c', 'core.eol=lf']
    if credential_helper:
        return command + ['-c', 'credential.helper=', '-c',
                          'credential.helper=' + ('' if credential_helper == 'none' else credential_helper)]
    if not url.startswith('https://github.com/'):
        return command
    gh = shutil.which('gh')
    if gh:
        try:
            auth = run_bounded([gh, 'auth', 'status', '--hostname', 'github.com'], 10)
            if auth.returncode == 0:
                helper = '!' + shlex.quote(gh.replace('\\', '/')) + ' auth git-credential'
                return command + ['-c', 'credential.helper=', '-c', 'credential.helper=' + helper]
        except CommandTimeout:
            progress('GitHub CLI状态检查超时，继续核对本机Git凭据助手')
    if sys.platform == 'win32':
        try:
            config = run_bounded([git, 'config', '--get-all', 'credential.helper'], 5)
            helpers = config.stdout.decode('utf-8', errors='replace').splitlines()
            if any('helper-selector' in value for value in helpers):
                manager = run_bounded([git, 'credential-manager', '--version'], 5)
                command += ['-c', 'credential.helper=']
                if manager.returncode == 0:
                    command += ['-c', 'credential.helper=manager']
                progress('已对本次命令绕过Windows helper-selector；未修改全局Git配置')
        except CommandTimeout as exc:
            raise InitError('凭据助手探测超时；可指定已安装Git路径与凭据助手后重试', 'credential_probe_timeout') from exc
    return command


def access_failure(result):
    error = result.stderr.decode('utf-8', errors='replace').lower()
    if any(item in error for item in ('connect tunnel failed', '502', 'could not resolve', 'failed to connect')):
        return InitError('网络或代理连接失败；先检查本次进程的代理设置，不反复尝试登录或索取密钥', 'network_failed')
    return InitError('未能访问目标库；核对GitHub登录、账号的仓库读取权限及网络。首次授权可能需用户在自己的交互终端完成，完成后重试', 'repository_access_failed')


def clone_repo(url, destination, git_executable=None, credential_helper=None,
               preflight_timeout=30, clone_timeout=180):
    progress(f'检查资料库访问：{destination.name}（最多{preflight_timeout}秒）')
    command = git_command(url, git_executable, credential_helper)
    try:
        access = run_bounded(command + ['ls-remote', '--', url, 'HEAD'], preflight_timeout)
    except CommandTimeout as exc:
        raise InitError('资料库访问检查超时；可能是凭据助手或网络阻塞，停止重试并检查环境', 'access_timeout') from exc
    if access.returncode:
        raise access_failure(access)
    progress(f'开始下载：{destination.name}（最多{clone_timeout}秒；保留原始换行字节）')
    try:
        result = run_bounded(command + ['clone', '--depth', '1', '--single-branch', '--no-tags', '--config', 'core.autocrlf=false',
                             '--config', 'core.eol=lf', '--', url, str(destination)], clone_timeout)
    except CommandTimeout as exc:
        raise InitError('下载超时，暂存目录保留；检查网络后可调大clone-timeout重试', 'clone_timeout') from exc
    if result.returncode:
        raise access_failure(result)


def modification_state(path, git_executable=None):
    git = str(git_executable) if git_executable else shutil.which('git')
    if not git or not (path / '.git').exists():
        return 'unknown'
    try:
        result = run_bounded([git, '-C', str(path), 'status', '--porcelain'], 10)
        return ('modified' if result.stdout else 'clean') if result.returncode == 0 else 'unknown'
    except (OSError, CommandTimeout):
        return 'unknown'


def initialize(root, **clone_options):
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
            clone_repo(REPOS[name], download, **clone_options)
            identity(download, name[len('timemix_'):])
            if os.path.lexists(target):
                raise InitError('下载期间目标目录已出现，停止以保护现有文件')
            download.rename(target)
            installed.append(name)
        except (InitError, DataError, OSError, ValueError, TypeError) as exc:
            done = '、'.join(installed) or '无'
            raise InitError(f'{name}初始化未完成：{exc}；已成功落盘的库：{done}（如有则保留）；暂存位置：{staging}',
                            getattr(exc, 'code', 'initialization_failed')) from exc
    if staging:
        staging.rmdir()
    progress('开始完整资料校验；校验通过不等于已完成内容审核')
    try:
        result = verify(root)
    except (DataError, OSError, ValueError, TypeError, KeyError) as exc:
        raise InitError(f'完整资料校验失败，停止售后处理，保留本地资料：{exc}') from exc
    result['installed'] = installed
    result['local_modifications'] = {name: modification_state(root / name, clone_options.get('git_executable')) for name in REPOS}
    return result


def timeout_seconds(value):
    seconds = int(value)
    if not 1 <= seconds <= 600:
        raise argparse.ArgumentTypeError('超时秒数须在1至600之间')
    return seconds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, help='Explicit local dataset root')
    parser.add_argument('--git-executable', type=Path, help='Use an already installed Git executable')
    parser.add_argument('--credential-helper', choices=('manager', 'osxkeychain', 'none'), help='Override helper for this operation only')
    parser.add_argument('--preflight-timeout', type=timeout_seconds, default=30)
    parser.add_argument('--clone-timeout', type=timeout_seconds, default=180)
    args = parser.parse_args()
    try:
        root = args.root or (Path(os.environ['TIMEMIX_DATA_ROOT'])
                            if os.environ.get('TIMEMIX_DATA_ROOT') else default_root())
        result = initialize(root, git_executable=args.git_executable,
                            credential_helper=args.credential_helper,
                            preflight_timeout=args.preflight_timeout, clone_timeout=args.clone_timeout)
    except (InitError, DataError, OSError, ValueError, TypeError) as exc:
        print(json.dumps({'ok': False, 'reason': str(exc),
                          'reason_code': getattr(exc, 'code', 'initialization_failed'),
                          'action': '暂停售后处理；解决所述问题后重新初始化并校验'}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
