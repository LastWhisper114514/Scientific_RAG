# -*- coding: utf-8 -*-
# src/ingestion/sample_raw.py
import argparse, gzip, json, os
from pathlib import Path

try:
    import ijson  # ???????
except Exception:
    ijson = None

from src.utils.pretty import log, ok, warn, section, timer

def _peek_first_nonspace_char_gz(path: str, max_read=8192) -> str:
    """?? gzip ??????????,??? JSONL ?? JSON array?"""
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
        buf = f.read(max_read)
    for ch in buf:
        if not ch.isspace():
            return ch
    return ""

def _iter_jsonl_gz(path: str):
    scanned = 0
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            scanned += 1
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj
    log(f"  [jsonl] scanned lines {scanned:,}")

def _iter_json_array_gz(path: str):
    if ijson is None:
        raise RuntimeError("??? JSON ????,???? ijson:?? `pip install ijson`")
    # ??:ijson ?????????
    with gzip.open(path, "rb") as f:
        for obj in ijson.items(f, "item"):
            if isinstance(obj, dict):
                yield obj

def sample_one_file(src_path: str, out_dir: str, limit: int = 200):
    p = Path(src_path)
    if not p.exists():
        warn(f"missing: {p}")
        return None

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (p.stem.replace(".json", "") + ".sample.jsonl")
    stats_file = out_dir / (p.stem.replace(".json", "") + ".stats.txt")

    section(f"Sample ? {p.name}")
    ch = _peek_first_nonspace_char_gz(str(p))
    fmt = "jsonl" if ch != "[" else "array"
    log(f"  detected format: {fmt}")

    it = _iter_jsonl_gz(str(p)) if fmt == "jsonl" else _iter_json_array_gz(str(p))

    kept = 0
    keys_union = set()
    examples = []

    with timer(f"write first {limit} dict objects to {out_file}"):
        with open(out_file, "w", encoding="utf-8") as w:
            for obj in it:
                # ???????
                if not isinstance(obj, dict):
                    continue
                if kept < 5:
                    examples.append({k: obj.get(k) for k in list(obj.keys())[:8]})
                keys_union.update(obj.keys())
                w.write(json.dumps(obj, ensure_ascii=False) + "\n")
                kept += 1
                if kept >= limit:
                    break

    with open(stats_file, "w", encoding="utf-8") as f:
        f.write(f"source: {p.name}\n")
        f.write(f"format: {fmt}\n")
        f.write(f"kept: {kept}\n")
        f.write(f"keys(total {len(keys_union)}): {sorted(list(keys_union))[:50]}\n")
        f.write("examples (up to 5, partial keys):\n")
        for i, ex in enumerate(examples, 1):
            f.write(f"  [{i}] {json.dumps(ex, ensure_ascii=False)}\n")

    ok(f"sample saved: {out_file}  | kept={kept}")
    ok(f"stats saved:  {stats_file}")
    return str(out_file)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=str, required=True, help="configs/ingestion_pwc.yaml")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--out_dir", type=str, default="data/pwc/raw/samples")
    args = ap.parse_args()

    import yaml
    cfg = yaml.safe_load(open(args.config, "r", encoding="utf-8"))
    raw_paths = cfg.get("raw_paths") or {}

    # ??????(?????)
    for name, path in raw_paths.items():
        if path:
            sample_one_file(path, args.out_dir, args.limit)

if __name__ == "__main__":
    main()
