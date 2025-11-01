# backend/src/core/topic_clusterer.py
from typing import List, Dict
import traceback

class TopicClusterer:
    """
    Cluster texts using sentence-transformers if available,
    fallback to TF-IDF + KMeans.
    """
    def __init__(self):
        self._embedder = None

    def _load_embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                print("Sentence-Transformer unavailable:", e)
                self._embedder = None
        return self._embedder

    def cluster(self, texts: List[str], n_clusters: int = 5) -> Dict[int, List[int]]:
        if not texts:
            return {}
        embedder = self._load_embedder()
        if embedder:
            try:
                embs = embedder.encode(texts, convert_to_numpy=True)
                from sklearn.cluster import KMeans
                k = min(n_clusters, len(texts))
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(embs).tolist()
                clusters = {}
                for i, lbl in enumerate(labels):
                    clusters.setdefault(int(lbl), []).append(i)
                return clusters
            except Exception:
                traceback.print_exc()
        # fallback: TF-IDF + KMeans
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.cluster import KMeans
            vect = TfidfVectorizer(stop_words="english", max_features=1000)
            X = vect.fit_transform(texts)
            k = min(n_clusters, len(texts))
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)
            clusters = {}
            for i, lbl in enumerate(labels):
                clusters.setdefault(int(lbl), []).append(i)
            return clusters
        except Exception:
            traceback.print_exc()
            # naive round-robin
            clusters = {}
            for i, _ in enumerate(texts):
                clusters.setdefault(i % n_clusters, []).append(i)
            return clusters
