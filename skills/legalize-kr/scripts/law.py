#!/usr/bin/env python3
"""Offline lookup over a local copy of the Legalize-KR laws dataset.

Standard library only. Reads the Markdown files under ``<data>/kr`` and prints JSON.

Data directory: ``--data`` or ``LEGALIZE_KR_DIR`` (default ``/opt/legalize-kr/current``).

A law folder can hold more than one file of the same kind. For example
``kr/근로기준법/`` has ``법률.md`` (a 1997 repeal notice) and ``법률(법률).md``
(the version in force), and every file says ``상태: 시행``. So the current
version is chosen from the frontmatter dates, never from the file name or ``상태``.

Commands:
  info                         dataset snapshot and counts
  find <name>                  law folders matching a name, with their current documents
  article <law> <article>      one article of the current document (e.g. 제60조, 60, 839조의2)
  search <keyword>             lines in current documents that contain the keyword
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_DATA = "/opt/legalize-kr/current"
KST = dt.timezone(dt.timedelta(hours=9))

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
ARTICLE_HEADING = re.compile(r"^#{1,6}\s*제(\d+)조(?:의(\d+))?(?:\s*\((.*?)\))?\s*$")
ARTICLE_QUERY = re.compile(r"^(?:제)?\s*(\d+)\s*(?:조)?\s*(?:의\s*(\d+))?$")


def data_dir(arg: str | None) -> Path:
    return Path(arg or os.environ.get("LEGALIZE_KR_DIR") or DEFAULT_DATA)


def read_frontmatter(path: Path) -> dict[str, str]:
    # The whole file, not a head: 603 files carry attachment lists that push the frontmatter past 4 KB
    # (up to 88 KB), and a cut frontmatter loses its dates, so the wrong version would look current.
    return parse_frontmatter(path.read_text(encoding="utf-8"))


def parse_frontmatter(head: str) -> dict[str, str]:
    m = FRONTMATTER.match(head)
    if not m:
        return {}
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "-")):
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip().strip("'\"")
    return meta


def doc_kind(path: Path) -> str:
    """``법률(법률).md`` and ``법률.md`` are the same kind: ``법률``."""
    return path.stem.split("(")[0]


def current_documents(folder: Path) -> list[dict]:
    """The newest document of each kind in a law folder."""
    best: dict[str, tuple[tuple[str, str], Path, dict[str, str]]] = {}
    for path in sorted(folder.glob("*.md")):
        meta = read_frontmatter(path)
        key = (meta.get("공포일자", ""), meta.get("시행일자", ""))
        kind = doc_kind(path)
        if kind not in best or key > best[kind][0]:
            best[kind] = (key, path, meta)
    today = dt.datetime.now(KST).date().isoformat()
    docs = []
    for kind, (_, path, meta) in sorted(best.items()):
        effective = meta.get("시행일자", "")
        docs.append({
            "kind": kind,
            "title": meta.get("제목", folder.name),
            "file": str(path),
            "promulgated": meta.get("공포일자", ""),
            "effective": effective,
            "not_yet_effective": bool(effective) and effective > today,
            "source": meta.get("출처", ""),
        })
    return docs


def law_folders(root: Path) -> list[Path]:
    kr = root / "kr"
    if not kr.is_dir():
        raise SystemExit(json.dumps({"error": "DATA_NOT_FOUND", "path": str(kr)}, ensure_ascii=False))
    return sorted(p for p in kr.iterdir() if p.is_dir())


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", "", name)


def match_folders(root: Path, name: str) -> list[Path]:
    want = normalize_name(name)
    folders = law_folders(root)
    exact = [p for p in folders if p.name == want]
    return exact or [p for p in folders if want in p.name]


def pick_document(folder: Path, kind: str | None) -> dict | None:
    docs = current_documents(folder)
    if kind:
        docs = [d for d in docs if d["kind"] == kind]
    elif any(d["kind"] == "법률" for d in docs):
        docs = [d for d in docs if d["kind"] == "법률"]
    return docs[0] if len(docs) == 1 else None if not docs else {"ambiguous": [d["kind"] for d in docs]}


def parse_article_query(text: str) -> tuple[int, int] | None:
    m = ARTICLE_QUERY.match(text.strip())
    if not m:
        return None
    return int(m.group(1)), int(m.group(2) or 0)


def iter_articles(path: Path):
    """Yield (number, sub, title, lines) for each article heading in a document."""
    current = None
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("#"):
                if current:
                    yield current
                m = ARTICLE_HEADING.match(line)
                current = (int(m.group(1)), int(m.group(2) or 0), m.group(3) or "", []) if m else None
                continue
            if current:
                current[3].append(line)
    if current:
        yield current


def article_label(num: int, sub: int) -> str:
    return f"제{num}조" + (f"의{sub}" if sub else "")


def cmd_info(root: Path) -> dict:
    folders = law_folders(root)
    files = sum(1 for p in folders for _ in p.glob("*.md"))
    snapshot = (root / "SNAPSHOT").read_text(encoding="utf-8").strip() if (root / "SNAPSHOT").exists() else ""
    return {"data": str(root), "snapshot": snapshot, "laws": len(folders), "files": files}


def cmd_find(root: Path, name: str, limit: int) -> dict:
    folders = match_folders(root, name)
    return {
        "query": name,
        "total": len(folders),
        "results": [{"law": p.name, "documents": current_documents(p)} for p in folders[:limit]],
    }


def cmd_article(root: Path, law: str, article: str, kind: str | None) -> dict:
    query = parse_article_query(article)
    if not query:
        return {"error": "BAD_ARTICLE", "article": article}
    folders = match_folders(root, law)
    if not folders:
        return {"error": "LAW_NOT_FOUND", "law": law}
    if len(folders) > 1 and folders[0].name != normalize_name(law):
        return {"error": "AMBIGUOUS_LAW", "law": law, "candidates": [p.name for p in folders[:20]]}
    doc = pick_document(folders[0], kind)
    if doc is None:
        return {"error": "KIND_NOT_FOUND", "law": folders[0].name, "kind": kind}
    if "ambiguous" in doc:
        return {"error": "AMBIGUOUS_KIND", "law": folders[0].name, "kinds": doc["ambiguous"]}
    for num, sub, title, lines in iter_articles(Path(doc["file"])):
        if (num, sub) == query:
            text = "\n".join(lines).strip()
            return {"law": folders[0].name, "article": article_label(num, sub), "heading": title, "text": text, "document": doc}
    return {"error": "ARTICLE_NOT_FOUND", "law": folders[0].name, "article": article_label(*query), "document": doc}


def cmd_search(root: Path, keyword: str, kind: str | None, limit: int) -> dict:
    """One read per file: pick the current document of each kind from the texts, then scan only those
    that contain the keyword. Reading every file twice made a full search take about a minute."""
    hits = []
    total = 0
    for folder in law_folders(root):
        best: dict[str, tuple[tuple[str, str], str]] = {}
        for path in sorted(folder.glob("*.md")):
            k = doc_kind(path)
            if kind and k != kind:
                continue
            text = path.read_text(encoding="utf-8")
            meta = parse_frontmatter(text)
            key = (meta.get("공포일자", ""), meta.get("시행일자", ""))
            if k not in best or key > best[k][0]:
                best[k] = (key, text)
        for k, (_, text) in sorted(best.items()):
            if keyword not in text:
                continue
            label = None
            for line in text.splitlines():
                if line.startswith("#"):
                    m = ARTICLE_HEADING.match(line)
                    label = article_label(int(m.group(1)), int(m.group(2) or 0)) if m else None
                    continue
                if label and keyword in line:
                    total += 1
                    if len(hits) < limit:
                        hits.append({"law": folder.name, "kind": k, "article": label, "line": line.strip()[:200]})
    return {"query": keyword, "total": total, "shown": len(hits), "results": hits}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", help=f"dataset directory (default: $LEGALIZE_KR_DIR or {DEFAULT_DATA})")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info")
    p = sub.add_parser("find")
    p.add_argument("name")
    p.add_argument("--limit", type=int, default=10)
    p = sub.add_parser("article")
    p.add_argument("law")
    p.add_argument("article")
    p.add_argument("--kind", help="법률, 시행령, 시행규칙 ... (default: 법률 when present)")
    p = sub.add_parser("search")
    p.add_argument("keyword")
    p.add_argument("--kind")
    p.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)

    root = data_dir(args.data)
    if args.cmd == "info":
        out = cmd_info(root)
    elif args.cmd == "find":
        out = cmd_find(root, args.name, args.limit)
    elif args.cmd == "article":
        out = cmd_article(root, args.law, args.article, args.kind)
    else:
        out = cmd_search(root, args.keyword, args.kind, args.limit)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 1 if "error" in out else 0


if __name__ == "__main__":
    sys.exit(main())
