"""
ai/engine.py

Semantic search, smart auto-grouping, and NL intent parsing.

Search priority:
  1. sentence-transformers (all-MiniLM-L6-v2) — semantic cosine similarity
  2. TF-IDF fallback — pure keyword scoring, zero extra deps
"""

import re
import math
import logging
from typing import List, Optional, Tuple
from collections import Counter

from core.window_manager import WindowInfo, classify_window

logger = logging.getLogger(__name__)

# ── Optional: sentence-transformers ─────────────────────────────────────────

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    ST_AVAILABLE = True
    logger.info("sentence-transformers available — semantic search enabled.")
except ImportError:
    ST_AVAILABLE = False
    logger.info("sentence-transformers not found — using TF-IDF fallback.")


# ── TF-IDF helpers ───────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _tfidf_score(query_tokens: List[str], doc_tokens: List[str], idf: dict) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    doc_freq = Counter(doc_tokens)
    doc_len = len(doc_tokens)
    score = 0.0
    for tok in query_tokens:
        tf = doc_freq.get(tok, 0) / max(doc_len, 1)
        score += tf * idf.get(tok, 0.0)
    return score


def _build_idf(docs: List[List[str]]) -> dict:
    N = len(docs)
    if N == 0:
        return {}
    df: Counter = Counter()
    for doc in docs:
        df.update(set(doc))
    return {tok: math.log((N + 1) / (cnt + 1)) + 1 for tok, cnt in df.items()}


# ── AI Engine class ──────────────────────────────────────────────────────────

class AIEngine:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model = None
        self._model_name = model_name
        self._embeddings = None
        self._windows: List[WindowInfo] = []

        if ST_AVAILABLE:
            try:
                logger.info("Loading embedding model: %s", model_name)
                self._model = SentenceTransformer(model_name)
                logger.info("Embedding model loaded.")
            except Exception as e:
                logger.warning("Could not load embedding model: %s", e)

    # ── Index update ─────────────────────────────────────────────────────────

    def update_index(self, windows: List[WindowInfo]) -> None:
        """Re-index all windows. Call whenever the window list changes."""
        self._windows = windows
        texts = [f"{w.title} {w.process_name}" for w in windows]

        if self._model and ST_AVAILABLE:
            try:
                import numpy as np
                self._embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                return
            except Exception as e:
                logger.warning("Embedding failed: %s — falling back to TF-IDF", e)

        # TF-IDF fallback
        self._docs = [_tokenize(t) for t in texts]
        self._idf = _build_idf(self._docs)
        self._embeddings = None

    # ── Semantic search ──────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 5) -> List[Tuple[WindowInfo, float]]:
        """Return top-k windows most relevant to the query, with scores."""
        if not self._windows:
            return []

        if self._model and ST_AVAILABLE and self._embeddings is not None:
            return self._search_semantic(query, top_k)
        return self._search_tfidf(query, top_k)

    def _search_semantic(self, query: str, top_k: int) -> List[Tuple[WindowInfo, float]]:
        import numpy as np
        q_emb = self._model.encode([query], convert_to_numpy=True)[0]
        norms = np.linalg.norm(self._embeddings, axis=1) * np.linalg.norm(q_emb)
        norms = np.where(norms == 0, 1e-9, norms)
        scores = (self._embeddings @ q_emb) / norms
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [(self._windows[i], float(scores[i])) for i in top_idx if scores[i] > 0.05]

    def _search_tfidf(self, query: str, top_k: int) -> List[Tuple[WindowInfo, float]]:
        q_tokens = _tokenize(query)
        scored = []
        for i, doc_tokens in enumerate(self._docs):
            sc = _tfidf_score(q_tokens, doc_tokens, self._idf)
            if sc > 0:
                scored.append((self._windows[i], sc))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    # ── Auto-grouping ─────────────────────────────────────────────────────────

    def auto_group_all(self, windows: List[WindowInfo]) -> List[WindowInfo]:
        """Reclassify all windows using keyword heuristics (instant, no model)."""
        for w in windows:
            w.group = classify_window(w.title, w.process_name)
        return windows

    # ── Intent parsing ────────────────────────────────────────────────────────

    PATTERNS = [
        (r"^find\s+(.+)$",                     "search"),
        (r"^search\s+(?:for\s+)?(.+)$",        "search"),
        (r"^open\s+(.+)$",                      "focus"),
        (r"^focus\s+(.+)$",                     "focus"),
        (r"^switch\s+to\s+(.+)$",              "switch_group"),
        (r"^show\s+(.+)\s+workspace$",          "switch_group"),
        (r"^close\s+(.+)$",                     "close"),
        (r"^minimize\s+(.+)$",                  "minimize"),
        (r"^save\s+session\s+(.+)$",            "save_session"),
        (r"^restore\s+session\s+(.+)$",         "load_session"),
        (r"^load\s+session\s+(.+)$",            "load_session"),
        (r"^auto[\s-]?group$",                  "auto_group"),
        (r"^group\s+all$",                      "auto_group"),
    ]

    def parse_intent(self, text: str) -> Tuple[str, str]:
        """
        Parse a natural language command.
        Returns (intent, argument) where intent is one of:
            search | focus | switch_group | close | minimize |
            save_session | load_session | auto_group | unknown
        """
        text = text.strip().lower()
        for pattern, intent in self.PATTERNS:
            m = re.match(pattern, text, re.IGNORECASE)
            if m:
                arg = m.group(1).strip() if m.lastindex else ""
                return intent, arg
        # Default: treat as search
        return "search", text
