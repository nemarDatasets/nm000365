#!/usr/bin/env python3
"""Lane J (IEEG033 Du-IN): download the Hugging Face dataset liulab-repository/Du-IN at a pinned revision.

Usage: laneJ_hf_acquire.py <tree.json> <api.json> <dest_dir> <receipt.json> [workers]
Stdlib only. Each file is fetched with curl (resume, retries) from
https://huggingface.co/datasets/<repo>/resolve/<sha>/<path>, then verified:
LFS files against the LFS sha256 oid and size, plain git files against the git blob sha1 and size.
Re-running skips files that already verify. Writes a receipt listing every file, size and checksums.
"""
import concurrent.futures as cf
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

REPO = 'liulab-repository/Du-IN'


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def gitsha1(p):
    data = Path(p).read_bytes()
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def verify(p, e):
    if not p.exists() or p.stat().st_size != e['size']:
        return None
    if e.get('lfs'):
        s = sha256(p)
        return {'sha256': s} if s == e['lfs']['oid'] else None
    s = gitsha1(p)
    return {'git_sha1': s, 'sha256': sha256(p)} if s == e['oid'] else None


def fetch(e, dest, rev):
    p = dest / e['path']
    p.parent.mkdir(parents=True, exist_ok=True)
    v = verify(p, e)
    if v:
        return e['path'], v, 'already'
    url = f'https://huggingface.co/datasets/{REPO}/resolve/{rev}/' + urllib.parse.quote(e['path'])
    for attempt in range(8):
        if p.exists() and p.stat().st_size > e['size']:
            p.unlink()
        subprocess.run(['curl', '-sSL', '--fail', '-C', '-', '--retry', '20', '--retry-all-errors',
                        '--retry-delay', '5', '--connect-timeout', '30', '-o', str(p), url], check=False)
        v = verify(p, e)
        if v:
            return e['path'], v, f'downloaded attempt {attempt + 1}'
        if p.exists() and p.stat().st_size >= e['size']:
            p.unlink()  # complete-size but wrong hash: restart from zero
        time.sleep(10 * (attempt + 1))
    return e['path'], None, 'FAILED'


def main():
    tree, api, dest, receipt = map(Path, sys.argv[1:5])
    workers = int(sys.argv[5]) if len(sys.argv) > 5 else 8
    rev = json.loads(api.read_text())['sha']
    files = [e for e in json.loads(tree.read_text()) if e['type'] == 'file']
    files.sort(key=lambda e: -e['size'])
    dest.mkdir(parents=True, exist_ok=True)
    out, failed = [], []
    with cf.ThreadPoolExecutor(workers) as ex:
        for path, v, how in ex.map(lambda e: fetch(e, dest, rev), files):
            print(time.strftime('%FT%T'), how, path, flush=True)
            e = next(x for x in files if x['path'] == path)
            rec = {'path': path, 'size': e['size'], 'git_oid': e['oid'],
                   'lfs_sha256': (e.get('lfs') or {}).get('oid'), 'verified': bool(v)}
            if v:
                rec.update(v)
            else:
                failed.append(path)
            out.append(rec)
    out.sort(key=lambda r: r['path'])
    receipt.write_text(json.dumps({
        'source': f'https://huggingface.co/datasets/{REPO}', 'revision': rev,
        'lastModified': json.loads(api.read_text()).get('lastModified'),
        'license_card': json.loads(api.read_text()).get('cardData', {}).get('license'),
        'files_expected': len(files), 'files_verified': len(files) - len(failed),
        'bytes_expected': sum(e['size'] for e in files),
        'bytes_verified': sum(r['size'] for r in out if r['verified']),
        'complete': not failed, 'failed': failed,
        'verification': 'LFS files: sha256 == LFS oid and size; git files: git blob sha1 == tree oid and size',
        'finished_utc': time.strftime('%FT%TZ', time.gmtime()), 'files': out}, indent=1) + '\n')
    print('COMPLETE' if not failed else f'FAILED {len(failed)}', flush=True)
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
