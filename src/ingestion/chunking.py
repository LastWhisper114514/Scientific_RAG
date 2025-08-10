import json
from pathlib import Path
from typing import Iterable, Dict
from src.utils.pretty import log, ok, section, timer

def read_jsonl(path: str) -> Iterable[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def write_chunks(docs_path: str, out_path: str, size: int = 1200, overlap: int = 200):
    section("Step 3/4  Chunking ? chunks/chunks.jsonl")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    docs = 0; chunks = 0
    with timer(f"chunk docs (size={size}, overlap={overlap})"):
        with open(out_path, "w", encoding="utf-8") as w:
            for rec in read_jsonl(docs_path):
                docs += 1
                text, doc_id, meta = rec["text"], rec["doc_id"], rec["meta"]
                i, n = 0, len(text)
                while i < n:
                    j = min(i + size, n)
                    chunk = text[i:j].strip()
                    if chunk:
                        w.write(json.dumps({
                            "chunk_id": f"{doc_id}_{i}",
                            "doc_id": doc_id,
                            "chunk_text": chunk,
                            "meta": meta
                        }, ensure_ascii=False) + "\n")
                        chunks += 1
                    if j == n: break
                    i = j - overlap if j - overlap > 0 else j
    ok(f"docs processed: {docs:,}  |  chunks written: {chunks:,}  ? {out_path}")
