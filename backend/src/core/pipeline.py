import re
from typing import List, Dict, Any, Optional
import networkx as nx
from transformers import pipeline, logging
import warnings
from nltk.tokenize import sent_tokenize
import nltk
import spacy
from .content_extractor import split_paragraphs, clean_text
from .graph_summarizer import GraphSummarizer
from .topic_clusterer import TopicClusterer

# Quiet noisy transformer warnings in terminal
logging.set_verbosity_error()
warnings.filterwarnings(
    "ignore",
    message=r"`clean_up_tokenization_spaces` was not set",
    category=FutureWarning,
)

class PipelineManager:
    def __init__(self):
        # Initialize NLTK
        try:
            nltk.data.find('tokenizers/punkt')
            # NLTK 3.9+ requires separate punkt_tab tables
            try:
                nltk.data.find('tokenizers/punkt_tab')
            except LookupError:
                nltk.download('punkt_tab', quiet=True)
            nltk.data.find('corpora/stopwords')
            nltk.data.find('vader_lexicon')
        except LookupError:
            nltk.download('punkt', quiet=True)
            nltk.download('punkt_tab', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('vader_lexicon', quiet=True)

        # Initialize SpaCy
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

        # Initialize transformers with explicit tokenization settings
        # Abstractive summarizer (downloads on first use)
        self.summarizer = None
        try:
            # Allow override via env var MODEL_SUMMARIZER (e.g., facebook/bart-large-cnn)
            import os
            model_name = os.getenv("MODEL_SUMMARIZER", "sshleifer/distilbart-cnn-12-6")
            enable = os.getenv("ENABLE_ABSTRACTIVE", "true").lower() not in {"0","false","no"}
            if enable:
                self.summarizer = pipeline(
                    "summarization",
                    model=model_name,
                    framework="pt"
                )
        except Exception as e:
            print(f"Abstractive summarizer init failed, using fallback: {e}")
            self.summarizer = None

        # T5 Title classifier (text2text)
        self.title_classifier = None
        try:
            import os
            clf_model = os.getenv(
                "MODEL_TITLE_CLASSIFIER",
                "mrm8488/t5-base-finetuned-news-title-classification"
            )
            enable_clf = os.getenv("ENABLE_T5_CLASSIFIER", "true").lower() not in {"0","false","no"}
            if enable_clf:
                self.title_classifier = pipeline(
                    "text2text-generation",
                    model=clf_model,
                    framework="pt"
                )
        except Exception as e:
            print(f"T5 classifier init failed, continuing without it: {e}")

        # Initialize clusterer
        self.clusterer = TopicClusterer()
        # Lightweight extractive summarizer as fallback
        self.extractive = GraphSummarizer()

    def summarize(self, texts: List[str], max_length: Optional[int] = None) -> List[str]:
        summaries = []
        for text in texts:
            if not text or len(text.strip()) < 50:
                # Always return a compact snippet, even for short text
                summaries.append((text or "")[:280])
                continue
                
            # Dynamic length calculation based on input
            words = text.split()
            input_length = len(words)
            suggested_length = input_length // 3  # Aim for 1/3 of input length
            dynamic_max = min(max(suggested_length, 20), 130)
            final_max = max_length or dynamic_max
            min_length = min(10, final_max - 1)
            
            try:
                if self.summarizer is not None:
                    summary = self.summarizer(
                        text, 
                        max_length=final_max,
                        min_length=min_length,
                        do_sample=False,
                        clean_up_tokenization_spaces=True
                    )[0]['summary_text']
                else:
                    # Fallback: extractive TextRank-style summary
                    summary = self.extractive.summarize(text, top_n=3)
                # Enforce a hard cap to keep cards tidy
                summaries.append((summary or "")[:400])
            except Exception as e:
                print(f"Summarization error: {e}")
                try:
                    summaries.append(self.extractive.summarize(text, top_n=2)[:400])
                except Exception:
                    sentences = sent_tokenize(text)
                    summaries.append(' '.join(sentences[:2])[:300])
                
        return summaries

    # ...rest of the existing code...

    # ...existing code for multi_document_summary...
    def multi_document_summary(self, texts: List[str], max_length: int = 200) -> str:
        # Summarize concatenated docs; fallback to extractive
        joined = "\n\n".join(texts)
        try:
            if self.summarizer is not None:
                out = self.summarizer(joined, max_length=max_length, min_length=max(10, max_length//4), do_sample=False)
                return out[0]['summary_text']
            return self.extractive.summarize(joined, top_n=4)
        except Exception as e:
            print(f"Multi-doc summarization error: {e}")
            return self.extractive.summarize(joined, top_n=3)

    def ner(self, texts: List[str]):
        try:
            res = []
            for t in texts:
                doc = self.nlp(t or "")
                res.append([{"text": ent.text, "label": ent.label_} for ent in doc.ents])
            return res
        except Exception:
            return [[] for _ in texts]

    # ...existing code for sentiment, keywords, cluster_texts...
    def sentiment(self, texts: List[str]):
        # delegate to VADER if available else transformers
        try:
            from nltk.sentiment import SentimentIntensityAnalyzer
            import nltk
            nltk.download("vader_lexicon", quiet=True)
            sid = SentimentIntensityAnalyzer()
            out = []
            for t in texts:
                s = sid.polarity_scores(t or "")
                c = s.get("compound", 0.0)
                label = "POSITIVE" if c >= 0.05 else ("NEGATIVE" if c <= -0.05 else "NEUTRAL")
                out.append({"label": label, "score": c, "detail": s})
            return out
        except Exception:
            try:
                from transformers import pipeline
                sent_pipe = pipeline("sentiment-analysis")
                out = []
                for t in texts:
                    r = sent_pipe(t[:512])
                    out.append(r[0] if r else {"label": "NEUTRAL", "score": 0.0})
                return out
            except Exception:
                return [{"label": "NEUTRAL", "score": 0.0} for _ in texts]

    def keywords(self, text: str, top_n: int = 20):
        if not text:
            return []
        tokens = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        freq = {}
        for t in tokens:
            freq[t] = freq.get(t, 0) + 1
        return [{"word": w, "count": c} for w, c in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:top_n]]

    def cluster_texts(self, texts: List[str], n_clusters: int = 5):
        return self.clusterer.cluster(texts, n_clusters=n_clusters)

    def generate_content_graph(self, articles: List[Dict]):
        G = nx.Graph()
        try:
            for idx, article in enumerate(articles):
                article_id = f"article_{idx}"
                G.add_node(article_id, 
                          type='article',
                          title=article.get('title', ''))
                
                entities = article.get('analysis', {}).get('entities', [])
                for entity in entities:
                    entity_id = f"entity_{entity['text']}"
                    G.add_node(entity_id, 
                             type='entity',
                             label=entity['text'],
                             entity_type=entity['label'])
                    G.add_edge(article_id, entity_id)
        except Exception as e:
            print(f"Graph generation error: {e}")
        return G

    def analyze_article(self, text: str, title: Optional[str] = None):
        txt = clean_text(text or "")
        try:
            # Calculate appropriate max_length based on input
            words = txt.split()
            max_length = min(max(len(words) // 2, 20), 130)
            
            summary = self.summarize([txt], max_length=max_length)[0]
            entities = self.ner([txt])[0]
            sentiment = self.sentiment([txt])[0]
            keywords = self.keywords(txt, top_n=20)
            category = None
            if self.title_classifier is not None and (title or "").strip():
                try:
                    prompt = title.strip()
                    # Some T5 classifiers expect a task prefix; keep it minimal if not provided
                    # e.g., "news title: {title}"
                    candidates = self.title_classifier(f"news title: {prompt}", max_length=8, num_beams=4)
                    raw = candidates[0]['generated_text'] if candidates else ""
                    label = (raw or "").strip()
                    category = {"label": label, "raw": raw}
                except Exception as e:
                    print(f"Title classification error: {e}")
            
            return {
                "summary": summary,
                "entities": entities,
                "sentiment": sentiment,
                "keywords": keywords,
                "category": category
            }
        except Exception as e:
            print(f"Analysis error: {e}")
            return {
                "summary": "",
                "entities": [],
                "sentiment": {"label": "NEUTRAL", "score": 0.0},
                "keywords": [],
                "category": None
            }