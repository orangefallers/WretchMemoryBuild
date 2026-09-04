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
        cls.production_root = DIST_ROOT / "production"
        cls.production_report = build_site(cls.data, environment="production")

    def test_backup_counts_match_declared_values(self):
        self.assertEqual(self.inspection["posts"], 205)
        self.assertEqual(self.inspection["posts_declared"], 205)
        self.assertEqual(self.inspection["comments"], 475)
        self.assertEqual(self.inspection["comments_declared"], 475)
        self.assertEqual(self.inspection["orphan_comments"], 0)

    def test_local_build_includes_non_public_posts(self):
        self.assertEqual(self.report["posts_generated"], 205)
        self.assertEqual(self.report["comments_generated"], 452)
        self.assertTrue(self.report["build_success"])
        for post in self.data["posts"]:
            output = self.output_root / "blog" / f"{post['slug']}.html"
            self.assertTrue(output.exists())

    def test_production_build_includes_masked_non_public_posts(self):
        self.assertEqual(self.production_report["posts_generated"], 205)
        self.assertEqual(self.production_report["comments_generated"], 452)
        self.assertTrue(self.production_report["build_success"])
        for post in self.data["posts"]:
            output = self.production_root / "blog" / f"{post['slug']}.html"
            self.assertTrue(output.exists())

    def test_non_public_post_uses_reading_confirmation_mask(self):
        protected_posts = [post for post in self.data["posts"] if post["visibility"] != "public"]
        self.assertEqual(sum(post["visibility"] == "hidden" for post in protected_posts), 5)
        self.assertEqual(sum(post["visibility"] == "draft" for post in protected_posts), 53)
        for post in protected_posts:
            output = self.production_root / "blog" / f"{post['slug']}.html"
            rendered = output.read_text(encoding="utf-8")
            self.assertIn('placeholder="輸入密碼"', rendered)
            self.assertIn('data-reading-mask', rendered)
            self.assertIn('data-protected-content hidden', rendered)
            self.assertIn('js/reading-mask.js', rendered)

        script = (self.production_root / "js" / "reading-mask.js").read_text(encoding="utf-8")
        self.assertIn('READING_PASSWORD = "111111"', script)

    def test_public_post_has_no_reading_confirmation_mask(self):
        post = next(post for post in self.data["posts"] if post["visibility"] == "public")
        output = self.production_root / "blog" / f"{post['slug']}.html"
        rendered = output.read_text(encoding="utf-8")
        self.assertNotIn('data-reading-mask', rendered)
        self.assertNotIn('data-protected-content', rendered)
        self.assertNotIn('js/reading-mask.js', rendered)

    def test_non_public_posts_have_no_list_excerpt(self):
        pages = [self.production_root / "index.html", *sorted((self.production_root / "page").glob("*/index.html"))]
        cards = []
        for page in pages:
            rendered = page.read_text(encoding="utf-8")
            cards.extend(
                section.split("</article>", 1)[0]
                for section in rendered.split('<article class="post-card">')[1:]
            )
        for post in self.data["posts"]:
            if post["visibility"] != "public":
                card = next(card for card in cards if f'blog/{post["slug"]}.html' in card)
                self.assertNotIn('class="post-summary"', card)
                self.assertIn('class="title-lock"', card)
                self.assertIn('點擊標題輸入密碼解鎖', card)

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
