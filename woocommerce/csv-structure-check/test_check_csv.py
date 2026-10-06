import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from check_csv import inspect_bytes, MAX_BYTES


class CSVStructureTests(unittest.TestCase):
    def test_valid_quoted_comma_and_multiline_description(self):
        raw = b'Name,Description,SKU\n"Shirt, blue","First line\nsecond line",S1\n'
        self.assertEqual({'status': 'ok', 'rows': 1, 'issues': []}, inspect_bytes(raw))

    def test_utf8_bom_and_unicode(self):
        self.assertEqual('ok', inspect_bytes(b'\xef\xbb\xbf' + 'Name,SKU\nÇay,T1\n'.encode())['status'])

    def test_invalid_encoding(self):
        self.assertEqual('invalid_utf8', inspect_bytes(b'Name,SKU\n\xff,T1\n')['issues'][0]['code'])

    def test_blank_missing_duplicate_and_casefold_headers(self):
        for raw, code in ((b'', 'missing_header'), (b'Name,,SKU\nA,B,C\n', 'empty_header'),
                          (b'Name, name \nA,B\n', 'duplicate_header')):
            self.assertIn(code, [i['code'] for i in inspect_bytes(raw)['issues']])

    def test_semicolon_file_requires_delimiter_review(self):
        self.assertIn('one_column_check_delimiter', [i['code'] for i in inspect_bytes(b'Name;SKU\nTea;T1\n')['issues']])

    def test_short_long_rows(self):
        result = inspect_bytes(b'Name,SKU\nA\nB,T2,extra\n')
        self.assertEqual([2, 3], [i['line'] for i in result['issues']])

    def test_malformed_quote_and_null_byte(self):
        self.assertIn('csv_syntax', [i['code'] for i in inspect_bytes(b'Name,SKU\n"unclosed,S1')['issues']])
        self.assertEqual('null_byte', inspect_bytes(b'Name,SKU\nA\x00,T1\n')['issues'][0]['code'])

    def test_bounded_bytes_and_issue_count(self):
        self.assertEqual('file_too_large', inspect_bytes(b'x'*(MAX_BYTES+1))['issues'][0]['code'])
        result = inspect_bytes(b'Name,SKU\n' + b'one\n'*150)
        self.assertEqual('issue_limit_reached', result['issues'][-1]['code'])
        self.assertLessEqual(len(result['issues']), 101)

    def test_cli_exit_read_only_and_no_row_values_exposed(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)/'input.csv';source.write_bytes(b'Name,SKU\nPRIVATE ROW VALUE\n')
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('check_csv.py')), str(source)], capture_output=True, text=True)
            self.assertEqual(1, result.returncode)
            self.assertEqual('review', json.loads(result.stdout)['status'])
            self.assertNotIn('PRIVATE ROW VALUE', result.stdout)
            self.assertEqual(before, hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(['input.csv'], [p.name for p in Path(tmp).iterdir()])

    def test_missing_file_fails_without_traceback(self):
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('check_csv.py')), '/nonexistent/csv-structure-input.csv'], capture_output=True, text=True)
        self.assertEqual(1, result.returncode)
        self.assertEqual('file_unreadable', json.loads(result.stdout)['issues'][0]['code'])
        self.assertEqual('', result.stderr)


if __name__ == '__main__':
    unittest.main()
