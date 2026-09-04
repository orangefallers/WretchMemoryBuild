import unittest

from wretch_revival.builder import build_site
from wretch_revival.normalizer import normalize_backup
from wretch_revival.paths import DIST_ROOT
from wretch_revival.sanitizer import sanitize_html
from wretch_revival.scanner import inspect_backup


class BackupPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inspection = inspect_backup(write_report=True)
        cls.data = normalize_backup()
        cls.output_root = DIST_ROOT / "local"
        cls.report = build_site(cls.data, environment="local")

    def test_backup_counts_match_declared_values(self):
        self.assertEqual(self.inspection["posts"], 205)
        self.assertEqual(self.inspection["posts_declared"], 205)
        self.assertEqual(self.inspection["comments"], 475)
        self.assertEqual(self.inspection["comments_declared"], 475)
        self.assertEqual(self.inspection["orphan_comments"], 0)

    def test_default_build_respects_visibility(self):
        self.assertEqual(self.report["posts_generated"], 147)
        self.assertEqual(self.report["comments_generated"], 402)
        self.assertTrue(self.report["build_success"])
        for post in self.data["posts"]:
            output = self.output_root / "blog" / f"{post['slug']}.html"
            self.assertEqual(output.exists(), post["visibility"] == "public")

    def test_public_missing_image_has_safe_placeholder(self):
        public_media_posts = [
            post
            for post in self.data["posts"]
            if post["visibility"] == "public" and post["media"]
        ]
        self.assertEqual(len(public_media_posts), 1)
        post = public_media_posts[0]
        output = self.output_root / "blog" / f"{post['slug']}.html"
        rendered = output.read_text(encoding="utf-8")
        self.assertIn("歷史圖片已遺失", rendered)
        self.assertNotIn("<img", rendered)
        self.assertNotIn("f8.wretch.yimg.com", rendered)


class SanitizerTests(unittest.TestCase):
    def test_removes_executable_html(self):
        source = '<p onclick="bad()">保留</p><script>alert(1)</script><a href="javascript:bad()">連結</a>'
        cleaned = sanitize_html(source)
        self.assertIn("保留", cleaned)
        self.assertNotIn("onclick", cleaned)
        self.assertNotIn("script", cleaned)
        self.assertNotIn("alert", cleaned)
        self.assertNotIn("javascript:", cleaned)


if __name__ == "__main__":
    unittest.main()
