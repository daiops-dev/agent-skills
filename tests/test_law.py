import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "legalize-kr" / "scripts"))

import law  # noqa: E402

DATA = str(Path(__file__).resolve().parent / "fixtures")


def run(*args: str) -> tuple[int, dict]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = law.main(["--data", DATA, *args])
    return code, json.loads(out.getvalue())


class CurrentVersionTest(unittest.TestCase):
    def test_picks_newest_document_not_plain_file_name(self):
        # 법률.md is a 1997 repeal notice; the version in force is 법률(법률).md, whose
        # frontmatter is longer than 4 KB because of its attachment list.
        _, out = run("find", "시험법")
        docs = {d["kind"]: d for d in out["results"][0]["documents"]}
        self.assertTrue(docs["법률"]["file"].endswith("법률(법률).md"))
        self.assertEqual(docs["법률"]["effective"], "2026-10-02")

    def test_flags_document_not_yet_effective(self):
        _, out = run("find", "시험법")
        docs = {d["kind"]: d for d in out["results"][0]["documents"]}
        self.assertTrue(docs["시행령"]["not_yet_effective"])
        self.assertFalse(docs["법률"]["not_yet_effective"])


class ArticleTest(unittest.TestCase):
    def test_article_forms(self):
        for query in ("제60조", "60조", "60"):
            code, out = run("article", "시험법", query)
            self.assertEqual(code, 0, query)
            self.assertEqual(out["article"], "제60조")
            self.assertEqual(out["heading"], "연차 유급휴가")
            self.assertIn("15일", out["text"])
            self.assertNotIn("나누어", out["text"])

    def test_sub_article(self):
        _, out = run("article", "시험법", "제60조의2")
        self.assertEqual(out["article"], "제60조의2")
        self.assertIn("나누어", out["text"])

    def test_missing_article_is_an_error(self):
        code, out = run("article", "시험법", "제999조")
        self.assertEqual(code, 1)
        self.assertEqual(out["error"], "ARTICLE_NOT_FOUND")

    def test_missing_law_is_an_error(self):
        code, out = run("article", "없는법", "제1조")
        self.assertEqual(code, 1)
        self.assertEqual(out["error"], "LAW_NOT_FOUND")

    def test_kind_option(self):
        _, out = run("article", "시험법", "제1조", "--kind", "시행령")
        self.assertIn("세부", out["text"])


class SearchTest(unittest.TestCase):
    def test_search_only_current_articles(self):
        _, out = run("search", "유급휴가")
        found = sorted((r["kind"], r["article"]) for r in out["results"])
        # The 부칙 line and the old 법률.md (which also has a 제60조) are not articles in force.
        self.assertEqual(found, [("법률", "제60조"), ("시행령", "제1조")])
        self.assertEqual(out["total"], 2)
        self.assertFalse(any("10일" in r["line"] for r in out["results"]))

    def test_search_kind_filter(self):
        _, out = run("search", "유급휴가", "--kind", "법률")
        self.assertEqual([r["article"] for r in out["results"]], ["제60조"])


if __name__ == "__main__":
    unittest.main()
