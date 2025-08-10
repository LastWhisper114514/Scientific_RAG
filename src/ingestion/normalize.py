import json, hashlib
from pathlib import Path
from typing import List, Dict, Any
from src.utils.pretty import log, ok, section, timer

def _hash_id(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:16]

def write_docs_jsonl(papers: List[Dict[str, Any]], out_path: str):
    section("Step 2/4  Normalize ? processed/docs.jsonl")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    kept = 0
    with timer(f"write processed to {out_path}"):
        with open(out_path, "w", encoding="utf-8") as f:
            for p in papers:
                title = (p.get("title") or "").strip()
                abstract = (p.get("abstract") or "").strip()
                if not (title or abstract):
                    continue
                text = (title + "\n\n" + abstract).strip()
                doc_id = _hash_id((p.get("source_id") or title) + p.get("url", ""))
                meta = {
                    "title": title,
                    "url": p.get("url", ""),
                    "code": p.get("code", ""),
                    "tasks": p.get("tasks", []),
                    "methods": p.get("methods", []),
                    "datasets": p.get("datasets", []),
                    "source_id": p.get("source_id", "")
                }
                f.write(json.dumps({"doc_id": doc_id, "text": text, "meta": meta}, ensure_ascii=False) + "\n")
                kept += 1
    ok(f"processed docs written: {kept:,}")
