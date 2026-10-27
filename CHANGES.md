# Changes from agent-skills

Based on [legalize-kr/agent-skills](https://github.com/legalize-kr/agent-skills) commit `1dc5d00`.
The original skill chooses between a hosted MCP server, `legalize-cli` (GitHub API) and a git clone.
This copy answers only from a local copy of the laws dataset, so it works with no internet and no key
in a DAIOps employee workspace, including an on-premises one.

## Added

| Path | Why |
|---|---|
| `daiops.yaml` | DAIOps installs the laws dataset (one pinned `legalize-kr/legalize-kr` commit, about 54 MB download, 291 MB unpacked) into `/opt/legalize-kr/current` |
| `skills/legalize-kr/scripts/law.py` | Offline lookup (`info`, `find`, `article`, `search`), standard library only, JSON output |
| `tests/test_law.py`, `tests/fixtures/` | Tests for `law.py` on a small fixture law |
| `NOTICE` and this file | |

## Removed

| Path | Why |
|---|---|
| `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `plugin.json`, `gemini-extension.json`, `scripts/`, `.github/workflows/release.yml` | Plugin packaging for other hosts |
| `.mcp.json` | Starts `legalize-mcp` through `uvx`, which needs the network |
| `skills/legalize-kr/references/access-options.md`, `references/mcp-workflows.md`, `scripts/select_access_mode.py`, `agents/openai.yaml` | Online access choices that do not apply offline |
| `tests/test_access_mode.py`, `test_claude_marketplace.py`, `test_mcp_contract_docs.py`, `test_plugin_artifact.py`, `test_temporal_semantics_docs.py` | Tests of the removed files |

## Modified

| File | Change |
|---|---|
| `skills/legalize-kr/SKILL.md` | Rewritten around `scripts/law.py` and the local data. Kept from the original: legal information, not advice; read the document before quoting; state the date basis; never invent a document. Added: no outcome prediction or drafting, a closing notice in Korean, and an explicit note that precedents, administrative rules and ordinances are not included |
| `skills/legalize-kr/references/data-layout.md` | Notes that one law folder can hold several files of the same kind and how the current one is chosen |
| `.github/workflows/validate.yml` | Compiles and tests `law.py` only |
| `README.md` | A short header pointing to the original repository, the licenses, and this file |

## Known limits

- The current version of each kind is chosen by `공포일자`, then `시행일자`, from the frontmatter. File names and `상태`
  are not used: 85 folders keep an older file such as `법률.md` next to the current `법률(법률).md`, and every file
  says `상태: 시행` (measured on `35a67af`, 2026-10-26).
- The upstream data repositories may be force-pushed. If the pinned commit disappears, the install step fails and
  the pin in `daiops.yaml` must move to a new commit.
