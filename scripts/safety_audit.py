#!/usr/bin/env python3
"""Fail closed on accidentally committed private files in publication inputs.

Pattern checks are defense in depth, not a guarantee of secret absence.
"""
from pathlib import Path
import re

UNSAFE_NAME = re.compile(r'(^\.env(?:\.|$)|\.pem$|\.key$|\.p12$|(^|[-_.])(secret|credential|password|private[-_]key)([-_.]|$)|\.sqlite[0-9]*$|\.db$)', re.I)
UNSAFE_VALUE = (
    re.compile(r'-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----'),
    re.compile(r'\bgh[pousr]_[A-Za-z0-9_]{20,}\b'),
    re.compile(r'\bgithub_pat_[A-Za-z0-9_]{30,}\b'),
    re.compile(r'\bsb_secret_[A-Za-z0-9_]{18,}\b'),
    re.compile(r'\bsk-proj-[A-Za-z0-9_-]{24,}\b'),
)


def audit_public_sources(root):
    root = Path(root)
    issues = []
    for folder in ('content', 'site'):
        location = root / folder
        if not location.is_dir() or location.is_symlink():
            issues.append(f'Missing or unsafe public directory: {folder}')
            continue
        for path in sorted(location.rglob('*')):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                issues.append(f'Symlink not allowed in public input: {relative}')
                continue
            if path.is_dir():
                continue
            if UNSAFE_NAME.search(path.name):
                issues.append(f'Credential-like filename in public input: {relative}')
                continue
            if path.stat().st_size > 2_000_000:
                issues.append(f'Unreviewed oversized file: {relative}')
                continue
            if path.suffix.lower() not in {'.json', '.css', '.html', '.md', '.txt', '.svg'}:
                issues.append(f'Unexpected public file type: {relative}')
                continue
            try:
                content = path.read_text(encoding='utf-8')
            except (UnicodeError, OSError):
                issues.append(f'Unreadable public text: {relative}')
                continue
            if any(pattern.search(content) for pattern in UNSAFE_VALUE):
                issues.append(f'Credential-like content in public input: {relative}')
    return issues


def main():
    for issue in (issues := audit_public_sources(Path(__file__).resolve().parents[1])):
        print('PUBLIC_RELEASE_BLOCKED:', issue)
    if issues:
        raise SystemExit(1)
    print('Public input audit passed (heuristic checks only).')


if __name__ == '__main__':
    main()
