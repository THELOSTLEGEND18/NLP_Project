# backend/src/core/topic_classifier.py
from typing import Dict, Any
import traceback

class TopicClassifier:
    """
    Uses T5 fine-tuned if available, else zero-shot BART.
    """
    def __init__(self):
        self._pipe = None
        self._mode = None

    def _load(self):
        if self._pipe is None:
            try:
                from transformers import pipeline as hf_pipeline
                try:
                    self._pipe = hf_pipeline("text2text-generation", model="mrm8488/t5-base-finetuned-news-title-classification")
                    self._mode = "t5"
                except Exception:
                    self._pipe = hf_pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
                    self._mode = "zero-shot"
            except Exception:
                self._pipe = None
        return self._pipe

    def classify(self, text: str) -> Dict[str, Any]:
        pipe = self._load()
        if pipe is None:
            return {"label": "UNKNOWN"}
        try:
            if self._mode == "zero-shot":
                labels = ['business','technology','science','health','sports','entertainment','politics','world']
                out = pipe(text, candidate_labels=labels)
                return {"label": out.get("labels", [None])[0], "scores": out.get("scores", [])}
            else:
                out = pipe(text)
                return {"generated": out}
        except Exception:
            traceback.print_exc()
            return {"error": "classification_failed"}
