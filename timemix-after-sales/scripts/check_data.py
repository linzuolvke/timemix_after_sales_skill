"""Read-only local TimeMix dataset gate. No network or third-party dependencies."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import sys

class DataError(Exception):
    pass

def read_text(path):
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeError) as exc:
        raise DataError(f'无法读取文件：{path.name} ({type(exc).__name__})') from exc
    if not text.strip():
        raise DataError(f'文件为空：{path.name}')
    return text

def load_json(path):
    try:
        result = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        raise DataError(f'JSON损坏：{path.name}') from exc
    if not isinstance(result, dict):
        raise DataError(f'JSON顶层类型错误：{path.name}')
    return result

def inside(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise DataError('资料路径必须是库内相对路径')
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise DataError(f'引用越出资料库：{relative}') from exc
    if not path.is_file():
        raise DataError(f'缺少必要文件：{relative}')
    return path

def frontmatter(text):
    if not text.startswith('---\n') or '\n---\n' not in text[4:]:
        raise DataError('缺少有效元数据')
    result = {}
    for line in text.split('---', 2)[1].strip().splitlines():
        if ': ' in line:
            key, val = line.split(': ', 1)
            result[key] = val.strip().strip('"\'')
    return result

def markdown_links(text):
    return re.findall(r'\]\(([^)]+)\)', text)

def check_links(root, path, text):
    for link in markdown_links(text):
        if '://' in link or link.startswith('#'):
            continue
        name = link.split('#', 1)[0]
        relative = os.path.relpath(path.parent / name, root)
        target = inside(root, relative)
        read_text(target) if target.suffix in ('.md', '.json') else target.read_bytes()

def identity(root, kind):
    meta = load_json(root / 'DATASET.json')
    if meta.get('dataset') != f'timemix_{kind}':
        raise DataError(f'{kind}资料身份或格式不符')
    required_schema = 1 if kind == 'rules' else 2
    if meta.get('schema_version') != required_schema:
        label = 'Rules' if kind == 'rules' else 'Cases'
        raise DataError(f'{label}本机格式{meta.get("schema_version", "未知")}，当前Skill需要格式{required_schema}，请明确更新资料库；保留现有目录')
    if not isinstance(meta.get('version'), str) or not meta['version']:
        raise DataError(f'{kind}缺少版本标识')
    required = meta.get('required_files')
    if not isinstance(required, list) or 'INDEX.md' not in required:
        raise DataError(f'{kind}必要文件清单不完整')
    for relative in required:
        path = inside(root, relative)
        load_json(path) if path.suffix == '.json' else read_text(path)
    index = read_text(root / 'INDEX.md')
    check_links(root, root / 'INDEX.md', index)
    return meta

def verify(root):
    root = root.expanduser().resolve()
    rules, cases = root / 'timemix_rules', root / 'timemix_cases'
    rm, cm = identity(rules, 'rules'), identity(cases, 'cases')
    rule_files = sorted((rules / 'current').glob('*.md'))
    if not rule_files:
        raise DataError('Rules缺少现行规则')
    rule_ids = set()
    for path in rule_files:
        text = read_text(path)
        head = frontmatter(text)
        rid = head.get('id', '')
        if not re.fullmatch(r'RULE_[A-Z_]+_\d+', rid) or head.get('status') != 'active' or rid in rule_ids:
            raise DataError(f'现行规则元数据错误：{path.name}')
        rule_ids.add(rid)
        check_links(rules, path, text)
    manifest = load_json(cases / 'MANIFEST.json')
    ids = manifest.get('case_ids')
    if not isinstance(ids, list) or not ids or len(set(ids)) != len(ids) or manifest.get('case_count') != len(ids):
        raise DataError('Cases编号或数量不一致')
    actual = {p.parent.name for p in cases.glob('CASE_*/case.md')}
    if actual != set(ids):
        raise DataError('Cases文件与清单不一致')
    if manifest.get('version') != cm['version']:
        raise DataError('Cases版本标识不一致')
    for cid in ids:
        if not re.fullmatch(r'CASE_\d{4}_\d{3}', cid):
            raise DataError('Case编号格式错误')
        path = inside(cases, f'{cid}/case.md')
        text = read_text(path)
        head = frontmatter(text)
        if head.get('case_id') != cid or head.get('status') != 'closed':
            raise DataError(f'Case身份或结案状态错误：{cid}')
        for key in ('title', 'legacy_ids', 'issue_type', 'tags', 'date'):
            if not head.get(key):
                raise DataError(f'Case缺少字段{key}：{cid}')
        if head.get('discretion') not in (None, 'granted', 'denied'):
            raise DataError(f'破例字段错误：{cid}')
        if 'owner_judgment' in head and not head.get('discretion'):
            raise DataError(f'老板判断缺少破例决定：{cid}')
        if head['date'] != 'null' and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', head['date']):
            raise DataError(f'Case日期格式错误：{cid}')
        for section in ('案件事实', '客户诉求', '实际处理结果', '处理依据'):
            if f'## {section}' not in text:
                raise DataError(f'Case缺少{section}：{cid}')
        record = cases / cid / 'records.md'
        if record.exists():
            record_text = read_text(record)
            if re.search(r'Files mentioned by the user|思考状态|^## (?:ChatGPT|Codex|AI分析)', record_text, re.M):
                raise DataError(f'实际记录混入AI讨论：{cid}')
            check_links(cases, record, record_text)
        check_links(cases, path, text)
    originals = manifest.get('files')
    if not isinstance(originals, list):
        raise DataError('缺少来源文件清单')
    seen = set()
    for item in originals:
        if not isinstance(item, dict) or item.get('path') in seen:
            raise DataError('来源清单条目错误或重复')
        path = inside(cases, item.get('path'))
        raw = path.read_bytes()
        if len(raw) != item.get('bytes') or hashlib.sha256(raw).hexdigest() != item.get('sha256'):
            raise DataError(f'来源校验失败：{path.name}')
        seen.add(item['path'])
    expected = {p.relative_to(cases).as_posix() for p in cases.glob('CASE_*/*.md')}
    if seen != expected:
        raise DataError('文字文件与完整性清单不一致')
    if any((cases / name).exists() for name in ('cases', 'chats', 'raw', 'sources')):
        raise DataError('Cases仍存在旧目录，请更新资料库')
    return {'ok': True, 'root': str(root), 'rules_version': rm['version'],
            'rules_content_state': rm.get('content_state', 'unknown'),
            'cases_version': cm['version'],
            'rule_count': len(rule_ids), 'case_count': len(ids), 'cases_schema_version': 2,
            'source_file_count': len(originals), 'remote_latest_verified': False}

def windows_documents():
    # CSIDL_PERSONAL resolves redirected Documents; never assume a fixed drive.
    buffer = ctypes.create_unicode_buffer(32768)
    result = ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer)
    if result != 0 or not buffer.value:
        raise DataError('无法定位Windows系统文档目录，请显式指定根目录')
    return Path(buffer.value)

def default_root():
    if sys.platform == 'darwin':
        return Path.home() / 'Documents/Obsidian/TimeMix'
    if sys.platform == 'win32':
        return windows_documents() / 'timemix/TimeMixData'
    raise DataError('此系统需显式指定资料根目录')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, help='Explicit local dataset root')
    args = parser.parse_args()
    try:
        root = args.root or (Path(os.environ['TIMEMIX_DATA_ROOT']) if os.environ.get('TIMEMIX_DATA_ROOT') else default_root())
        result = verify(root)
    except (DataError, OSError, TypeError, ValueError, KeyError) as exc:
        print(json.dumps({'ok': False, 'reason': str(exc), 'action': '停止售后处理，修复本地资料或读取权限后重试'}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
