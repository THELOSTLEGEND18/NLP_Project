# backend/src/core/content_extractor.py
import re
from typing import List
import nltk

# ensure punkt exists if not already
try:
    nltk.data.find("tokenizers/punkt")
except Exception:
    nltk.download("punkt", quiet=True)
from nltk.tokenize import sent_tokenize

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"http\S+", "", text)             # remove urls
    text = re.sub(r"<[^>]+>", " ", text)            # remove tags
    # remove NewsAPI truncation markers like "[+1234 chars]"
    text = re.sub(r"\[\+\s?\d+\s?chars\]", "", text)
    text = re.sub(r"\(\+\s?\d+\s?chars\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def split_paragraphs(text: str, max_chars: int = 1000) -> List[str]:
    if not text:
        return []
    sents = sent_tokenize(text)
    chunks = []
    cur = ""
    for s in sents:
        if len(cur) + len(s) + 1 <= max_chars:
            cur = (cur + " " + s).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)
    return chunks
