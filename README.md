# Scientific_RAG
SciRAG is an open-source Retrieval-Augmented Generation (RAG) pipeline designed for AI researchers and practitioners.   It combines state-of-the-art retrieval with powerful large language models to help you quickly find, understand, and summarize scientific literature. 

---

## Features
- Full Papers with Code dataset ingestion — Automatically process metadata, abstracts, and research tasks.
- Chunking — Split papers into retrieval-friendly chunks for better relevance.
- Vector Search — Use FAISS for efficient similarity search.
- RAG Pipeline — Combine retrieval results with an LLM for context-aware answers.
- Extensible — Easily plug in your own models for encoding or generation.

---

## Project Structure

SciRAG/  
├── configs/ # YAML configs for ingestion, retrieval, and generation  
├── data/ # Dataset storage  
│ └── pwc/  
│ ├── raw/ # Original downloaded dataset  
│ ├── processed/ # After ingestion & cleaning  
│ └── chunks/ # Retrieval-ready text chunks  
├── models/  
│ ├── pretrained/ # Pre-trained LLM & encoder checkpoints  
│ └── finetuned/ # Fine-tuned models  
├── notebooks/ # Jupyter notebooks for experiments  
├── src/ # Source code for ingestion, retrieval, generation  
├── docs/ # Documentation and guides  
└── README.md  




---

## Quickstart

### 1. Clone & Install
```bash
git clone https://github.com/YourUsername/SciRAG.git
cd SciRAG
conda create -n rag python=3.11
conda activate rag
pip install -r requirements.txt
```

### 2.Download Dataset
Follow [Papers with Code Datasets](https://github.com/paperswithcode/paperswithcode-data), download following files:

 - papers-with-abstracts.json.gz  
 - links-between-papers-and-code.json.gz  
 - methods.json.gz  
 - datasets.json.gz  
 - evaluation-tables.json.gz  

and place those files under:

```bash
data/pwc/raw/
```

### 3.Data Processing

After downloading the raw dataset, the next step is to process it into a clean, retrieval-ready format. This involves the following steps:

1. **Load Raw Data**  
   - Merge abstracts and metadata from multiple JSONL.GZ files.
   - Link code repositories, methods, datasets, and evaluation tables to each paper.
   - Implemented with streaming JSON parsing (`ijson`) to reduce memory usage.

2. **Normalize Data**  
   - Apply a consistent schema to all records.
   - Standardize key fields such as `title`, `abstract`, `authors`, `methods`, and `tasks`.
   - Store all documents in a unified `docs.jsonl` format for downstream processing.

3. **Chunking**  
   - Split long documents into smaller text segments ("chunks") suitable for retrieval.
   - Chunks are typically 300–500 tokens each.
   - Proper chunking improves retrieval granularity and re-ranking performance.

4. **Build Index**  
   - Encode each chunk into dense vector embeddings using a pre-trained model.
   - Store embeddings in a FAISS index for efficient similarity search.

### 4.Run the Pipeline

From the project root, execute:

```bash
export PYTHONPATH=$(pwd)

python - <<'PY'
import yaml
from src.ingestion.load_pwc import load_papers
from src.ingestion.normalize import write_docs_jsonl

cfg = yaml.safe_load(open('configs/ingestion_pwc.yaml'))
papers = load_papers(cfg["raw_paths"])
print(f">>> papers loaded: {len(papers)}")
write_docs_jsonl(papers, cfg["processed_path"])
print(f">>> processed written to: {cfg['processed_path']}")
PY
```

Once normalization is complete, run chunking:
```bash
python src/ingestion/chunking.py \
    --config configs/ingestion_pwc.yaml
```

Finally, build the FAISS index:

```bash
python src/ingestion/build_index.py \
    --config configs/ingestion_pwc.yaml
```

Processed files will be saved in:
```bash
data/pwc/processed/   # Cleaned JSONL documents
data/pwc/chunks/      # Chunked text segments
data/pwc/index/       # FAISS index files

```


