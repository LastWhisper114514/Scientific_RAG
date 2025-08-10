import json, os, pickle, numpy as np, faiss
from pathlib import Path
from typing import Iterable, Dict
from sentence_transformers import SentenceTransformer
from src.utils.pretty import log, ok, section, timer, warn

def read_jsonl(path: str) -> Iterable[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)

def build_faiss(chunks_path: str, out_dir: str, embed_model: str = "BAAI/bge-m3",
                normalize: bool = True, device: str = "auto"):
    section("Step 4/4  Build FAISS index")
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    texts, metas, ids = [], [], []
    with timer(f"load chunks from {chunks_path}"):
        for rec in read_jsonl(chunks_path):
            texts.append(rec["chunk_text"])
            metas.append({"chunk_id": rec["chunk_id"], "doc_id": rec["doc_id"], **rec["meta"]})
            ids.append(rec["chunk_id"])
    if not texts:
        warn("no chunks found. skip index build.")
        return

    ok(f"chunks loaded: {len(texts):,}")

    with timer(f"encode embeddings with {embed_model} (normalize={normalize})"):
        model = SentenceTransformer(embed_model, device=None if device=="cpu" else ("cuda" if device=="auto" else device))
        embs = model.encode(texts, batch_size=64, show_progress_bar=True,
                            convert_to_numpy=True, normalize_embeddings=normalize)

    d = embs.shape[1]
    with timer(f"build FAISS IP index (dim={d})"):
        index = faiss.IndexFlatIP(d)
        index.add(embs.astype(np.float32))

    with timer(f"save index to {out_dir}"):
        faiss.write_index(index, os.path.join(out_dir, "index.faiss"))
        with open(os.path.join(out_dir, "ids.npy"), "wb") as f:
            np.save(f, np.array(ids))
        with open(os.path.join(out_dir, "docstore.pkl"), "wb") as f:
            pickle.dump(metas, f)
        with open(os.path.join(out_dir, "stats.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"count": int(len(texts)), "dim": int(d), "normalize": bool(normalize)}, ensure_ascii=False))
    ok(f"index ready: vectors={len(texts):,}, dim={d}, dir={out_dir}")
