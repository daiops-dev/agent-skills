import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class MCPContractDocsTest(unittest.TestCase):
    def test_remote_guides_use_current_sites_service(self) -> None:
        for path in ("README.md", "skills/legalize-kr/SKILL.md", "skills/legalize-kr/references/access-options.md"):
            text = (ROOT / path).read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertIn("https://chatgpt.legalize.kr", text)
                self.assertIn("OAuth", text)
                self.assertNotIn("mcp.legalize.kr", text)
                self.assertNotIn("MCP_API_KEY", text)
                self.assertNotIn("has not adopted 2.0", text)
                self.assertNotIn("not covered by this 2.0", text)

    def test_docs_separate_mcp_2_and_cli_1(self) -> None:
        skill = (ROOT / "skills/legalize-kr/SKILL.md").read_text(encoding="utf-8")
        for marker in ('schema_version: "2.0"', 'schema_version: "1.0"',
                       "laws_diff", "version.*", "source.*", "warnings[]",
                       "PATH_SEARCH_ONLY", "PARTIAL_SEARCH", "AMBIGUOUS_MATCH"):
            with self.subTest(marker=marker):
                self.assertIn(marker, skill)

    def test_sites_access_uses_host_oauth_and_personal_keys(self) -> None:
        text = (ROOT / "skills/legalize-kr/references/access-options.md").read_text(encoding="utf-8")
        sites = text.split("### Remote MCP through OpenAI Sites", 1)[1].split("## Git Clone Patterns", 1)[0]
        for marker in ("OAuth resource", "Created by", "personal GitHub key", "AUTH_REQUIRED", "https://chatgpt.legalize.kr/settings", "not shared with other users"):
            with self.subTest(marker=marker):
                self.assertIn(marker, sites)

    def test_law_paths_preserve_selected_family(self) -> None:
        skill = (ROOT / "skills/legalize-kr/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("returned full path as `law_name`", skill)
        self.assertNotIn("Do not pass a repository path as `law_name`", skill)
        workflow = (ROOT / "skills/legalize-kr/references/mcp-workflows.md").read_text(encoding="utf-8")
        self.assertIn("ask the user to select a returned path", workflow)

    def test_manifests_pin_same_cli(self) -> None:
        pin = "legalize-cli[mcp]==0.5.3"
        mcp = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
        gemini = json.loads((ROOT / "gemini-extension.json").read_text(encoding="utf-8"))
        self.assertEqual(mcp["mcpServers"]["legalize-kr"]["args"][1], pin)
        self.assertEqual(gemini["mcpServers"]["legalize-kr"]["args"][1], pin)
        self.assertIn(pin, (ROOT / "README.md").read_text(encoding="utf-8"))

    def test_full_titles_keep_published_cli_guidance(self) -> None:
        workflow = (ROOT / "skills/legalize-kr/references/mcp-workflows.md").read_text(encoding="utf-8")
        self.assertIn("주택도시기금법 시행령", workflow)
        self.assertIn("Earlier CLI releases require separate name and category", workflow)
