import os, json, pickle, numpy as np, faiss
from pathlib import Path
from sentence_transformers import SentenceTransformer
from src.utils.pretty import section, log, ok, timer

def load_index(index_dir: str):
    section("Load index")
    with timer(f"read FAISS from {index_dir}"):
        index = faiss.read_index(os.path.join(index_dir, "index.faiss"))
        ids = np.load(os.path.join(index_dir, "ids.npy"), allow_pickle=True)
        metas = pickle.load(open(os.path.join(index_dir, "docstore.pkl"), "rb"))
    ok(f"index loaded: vectors={len(ids):,}, dim={index.d}")
    id2meta = {m["chunk_id"]: m for m in metas}
    return index, ids, id2meta

def search(query: str, index_dir: str, embed_model="BAAI/bge-m3", top_k=6):
    index, ids, id2meta = load_index(index_dir)
    section("Search")
    with timer(f"embed query with {embed_model}"):
        enc = SentenceTransformer(embed_model)
        q = enc.encode([query], normalize_embeddings=True)
    with timer(f"FAISS search top_k={top_k}"):
        D, I = index.search(q.astype(np.float32), top_k)
    out = []
    for score, idx in zip(D[0], I[0]):
        cid = ids[idx]
        m = id2meta[cid]
        out.append({"score": float(score), "meta": m})
    ok(f"hits: {len(out)}")
    return out

if __name__ == "__main__":
    INDEX = "./indexes/pwc/bge-m3/faiss"
    TOPK = 6
    query = input("Query: ").strip()
    hits = search(query, INDEX, top_k=TOPK)
    print("\n== Top hits ==")
    for i, h in enumerate(hits, 1):
        m = h["meta"]
        print(f"[{i}] score={h['score']:.3f} | {m.get('title','')}")
        print(f"    url={m.get('url','')}")
