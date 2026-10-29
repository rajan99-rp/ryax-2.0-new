# RayX Model 2 — Enhanced Local Hybrid Edition

RayX is a local-first learning project. This package preserves the existing byte-level Transformer and checkpoints, and routes questions through several local components before neural generation.

## What is included

- Existing model architecture and checkpoints in `artifacts/` and `backups/`
- Training/data scripts: `train.py`, `prepare_data.py`, `generate.py`
- Hybrid chat: `rayx_auto.py`, `rayx_hybrid.py`
- Local calculator: `rayx_math_engine.py`
- Local JSONL knowledge base: `rayx_knowledge.py`, `knowledge/knowledge.jsonl`
- Saved-example memory: `rayx_memory.py`, `knowledge_memory.json`
- Self-improvement experiment: `rayx_self_improve.py`
- Existing datasets, logs, and tests folder

## Run

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m py_compile model.py rayx_auto.py rayx_memory.py rayx_hybrid.py rayx_knowledge.py rayx_math_engine.py train.py
python rayx_auto.py
```

Ask a question in the terminal. Type `exit` to stop.

## How answers are routed

1. Calculator for supported arithmetic expressions.
2. Local knowledge JSONL search.
3. High-threshold saved-example memory lookup.
4. Existing local neural model as a fallback.

Answers from the neural model are marked as not independently verified. The starter knowledge file is small and its records should be checked against reliable textbooks/sources before setting `verified: true`.

## Train carefully

The included model is a small byte-level Transformer, not a general-purpose pretrained LLM. It can generate incoherent text when a question is outside its limited training data. A larger dataset, cleaner examples, tests, and compute are needed for major capability gains.

Before training, keep a separate backup of checkpoints. To train with the existing pipeline:

```bash
python prepare_data.py
python train.py --steps 500
```

Do not assume a lower training loss proves factual correctness. Test against held-out questions and keep the best checkpoint if validation quality worsens.

## No external AI APIs

The chat path in this project does not call external AI APIs. PyTorch is required for the neural model. Network access is only needed if you choose to install packages or obtain your own training materials.

## Security and portability

- `.venv` is intentionally not included in portable archives; recreate it on each computer.
- Do not commit `.env` files, passwords, API keys, or private data.
- Existing checkpoints are retained. The hybrid chat does not overwrite checkpoints.
