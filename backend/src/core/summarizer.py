# backend/src/core/summarizer.py
from typing import List
import traceback

class Summarizer:
    """
    Wrapper for Pegasus/XSUM summarizer with fallback to DistilBART.
    Loads lazily.
    """
    def __init__(self):
        self._pipe = None
        self._model_name = None

    def _load(self):
        if self._pipe is None:
            try:
                from transformers import pipeline
                # prefer Pegasus
                try:
                    self._pipe = pipeline("summarization", model="google/pegasus-xsum", framework="pt")
                    self._model_name = "pegasus-xsum"
                except Exception:
                    self._pipe = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", framework="pt")
                    self._model_name = "distilbart"
            except Exception as e:
                print("Summarizer load failed:", e)
                self._pipe = None
        return self._pipe

    def summarize(self, texts: List[str], max_length: int = 160) -> List[str]:
        pipe = self._load()
        out = []
        if pipe is None:
            # fallback: simple trim
            for t in texts:
                out.append(t[:300] + ("..." if len(t) > 300 else ""))
            return out

        for t in texts:
            if not t:
                out.append("")
                continue
            try:
                # chunk if too long (simple char chunks)
                max_chunk = 1500
                if len(t) > max_chunk:
                    chunks = [t[i:i+max_chunk] for i in range(0, len(t), max_chunk)]
                    chunk_summaries = []
                    for c in chunks:
                        r = pipe(c, max_length=max_length, min_length=30, truncation=True)
                        chunk_summaries.append(r[0].get("summary_text") if isinstance(r, list) and r else str(r))
                    joined = " ".join(chunk_summaries)
                    r2 = pipe(joined, max_length=max_length, min_length=30, truncation=True)
                    out.append(r2[0].get("summary_text") if isinstance(r2, list) and r2 else joined[:max_length])
                else:
                    r = pipe(t, max_length=max_length, min_length=30, truncation=True)
                    out.append(r[0].get("summary_text") if isinstance(r, list) and r else str(r))
            except Exception:
                traceback.print_exc()
                out.append(t[:300] + ("..." if len(t) > 300 else ""))
        return out
