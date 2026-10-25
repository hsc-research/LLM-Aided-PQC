"""Offline regression checks for local documentation links."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import check_docs


class DocumentationLinks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'docs').mkdir()

    def check(self):
        with patch.object(check_docs, 'ROOT', self.root), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            return check_docs.main()

    def test_inline_html_reference_and_duplicate_headings(self):
        (self.root / 'docs/page.md').write_text('# Same\n# Same\n')
        (self.root / 'README.md').write_text(
            '[page](docs/page.md#same-1)\n'
            '<a href="docs/page.md#same">link</a>\n'
            '[ref]: docs/page.md\n')
        self.assertEqual(self.check(), 0)

    def test_missing_target_fails(self):
        (self.root / 'README.md').write_text('[missing](docs/no.md)\n')
        self.assertEqual(self.check(), 1)

    def test_missing_heading_fails(self):
        (self.root / 'README.md').write_text('# Present\n[missing](#absent)\n')
        self.assertEqual(self.check(), 1)

    def test_code_and_external_links_not_checked(self):
        (self.root / 'README.md').write_text(
            '```text\n[example](not-a-file)\n```\n'
            '[web](https://example.invalid/no-network)\n')
        self.assertEqual(self.check(), 0)

    def test_image_and_explicit_anchor(self):
        (self.root / 'docs/image.svg').write_text('<svg/>')
        (self.root / 'README.md').write_text(
            '![image](docs/image.svg)\n'
            '<span id="named"></span>\n[anchor](#named)\n')
        self.assertEqual(self.check(), 0)


if __name__ == '__main__':
    unittest.main()
