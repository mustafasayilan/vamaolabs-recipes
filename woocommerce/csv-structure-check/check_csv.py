"""Read-only UTF-8 CSV structure check. No import, catalog access or network calls."""
import argparse
import csv
import io
import json
from pathlib import Path

MAX_BYTES = 10 * 1024 * 1024


def inspect_bytes(raw):
    if len(raw) > MAX_BYTES:
        return {'status': 'error', 'rows': None, 'issues': [{'line': None, 'code': 'file_too_large'}]}
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return {'status': 'error', 'rows': None, 'issues': [{'line': None, 'code': 'invalid_utf8'}]}
    if '\x00' in text:
        return {'status': 'error', 'rows': None, 'issues': [{'line': None, 'code': 'null_byte'}]}
    reader = csv.reader(io.StringIO(text, newline=''), strict=True)
    issues, rows = [], 0
    try:
        header = next(reader, None)
        if not header:
            return {'status': 'error', 'rows': 0, 'issues': [{'line': 1, 'code': 'missing_header'}]}
        names = [name.strip().casefold() for name in header]
        if any(not name for name in names):
            issues.append({'line': 1, 'code': 'empty_header'})
        if len(names) != len(set(names)):
            issues.append({'line': 1, 'code': 'duplicate_header'})
        if len(header) == 1:
            issues.append({'line': 1, 'code': 'one_column_check_delimiter'})
        for record in reader:
            # Entirely blank physical lines are ignored by csv.reader.
            rows += 1
            if len(record) != len(header):
                issues.append({'line': reader.line_num, 'code': 'column_count', 'expected': len(header), 'actual': len(record)})
            if len(issues) >= 100:
                issues.append({'line': reader.line_num, 'code': 'issue_limit_reached'})
                break
    except csv.Error:
        issues.append({'line': reader.line_num, 'code': 'csv_syntax'})
    return {'status': 'review' if issues else 'ok', 'rows': rows, 'issues': issues}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_file', type=Path)
    args = parser.parse_args()
    try:
        with args.csv_file.open('rb') as handle:
            raw = handle.read(MAX_BYTES + 1)
        result = inspect_bytes(raw)
    except OSError:
        result = {'status': 'error', 'rows': None, 'issues': [{'line': None, 'code': 'file_unreadable'}]}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result['status'] == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
