# backend/src/core/graph_summarizer.py
from typing import List
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class GraphSummarizer:
    """
    Extractive summarizer using sentence similarity + PageRank (TextRank-style).
    """
    def summarize(self, text: str, top_n: int = 3) -> str:
        if not text:
            return ""
        sentences = [s.strip() for s in text.split('.') if len(s.split()) > 3]
        if not sentences:
            return text
        if len(sentences) <= top_n:
            return ". ".join(sentences)

        vect = TfidfVectorizer(stop_words='english')
        X = vect.fit_transform(sentences)
        sim = cosine_similarity(X, X)
        nx_graph = nx.from_numpy_array(sim)
        scores = nx.pagerank(nx_graph)
        ranked = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
        selected = [s for _, s in ranked[:top_n]]
        return ". ".join(selected)
