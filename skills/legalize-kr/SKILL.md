---
name: legalize-kr
description: Look up Korean laws (법률 · 시행령 · 시행규칙 and other statutes) in a local, offline copy of the Legalize-KR dataset. Use it to find a law, read one article, or search articles by keyword, and answer with the article text and its effective date. Works without internet or API keys.
---

# Korean law lookup (offline)

The laws are a local copy of `legalize-kr/legalize-kr`: Markdown files under `kr/<law name without spaces>/`,
one file per kind (`법률`, `시행령`, `시행규칙`, `대통령령`, ...). The copy was taken on one date and does not update.

This is legal information, not legal advice.

## Tool

Use only `scripts/law.py` in this skill folder. It prints JSON. Do not read the data folder with other commands
unless the script cannot answer.

```bash
python3 scripts/law.py info                                  # snapshot date and counts
python3 scripts/law.py find 근로기준법                         # law folders and their current documents
python3 scripts/law.py article 근로기준법 제60조                # one article of the 법률
python3 scripts/law.py article 근로기준법 제30조 --kind 시행령    # one article of another kind
python3 scripts/law.py search 연차 --limit 20                  # article lines containing a keyword
```

- Law names have no spaces in folder names (`근로기준법`, `개인정보보호법`). If `article` returns `LAW_NOT_FOUND`
  or `AMBIGUOUS_LAW`, run `find` with a shorter name and pick from the candidates.
- `article` accepts `제60조`, `60조`, `60`, `제839조의2`.
- `search` matches the exact string. Try a shorter word or a different word for the same idea before saying
  nothing was found. It skips 부칙 and old versions.
- Exit code 1 with an `error` field means the lookup failed. Report it as a failure, not as "the law says nothing".

## How to answer

1. Find the law and read the article before you quote or summarize it. A search hit is only a candidate.
2. Quote the article text as it is, then explain it in plain words. Keep the two apart.
3. End with a source line: the law title, the article, `effective` (시행일자) and the snapshot date from `info`.
   If `not_yet_effective` is true, say the text is promulgated but not yet in force.
4. If the article or law is not in the data, say so. Never write an article number, a 판례 number or a date that
   you did not read from the tool output.
5. Answer in the user's language.
6. Close with: 「법령 정보 안내이며 법률 자문이 아닙니다. 구체적인 사건은 변호사와 상담하세요.」 (or the same
   sentence in the user's language).

## What not to do

- Do not predict who wins a dispute, estimate damages, or draft complaints, contracts or other legal documents.
  Offer the relevant articles instead and suggest a lawyer.
- Do not answer from memory when the tool can be used. Laws change; the data has the dated text.
- The dataset has no court precedents (판례), administrative rules or local ordinances. Say so if asked.
- File-level dates only: the tool does not decide article-specific commencement dates or transitional rules
  in 부칙.

See `references/data-layout.md` for the file layout and frontmatter fields.
