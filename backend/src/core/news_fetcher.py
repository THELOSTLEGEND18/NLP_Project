import requests
import re
from typing import List, Dict, Any
from datetime import datetime, timedelta

class NewsFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)
        # bump this to invalidate old cached responses after logic changes
        self.cache_version = "v3"
        # NewsAPI supported categories
        self.supported_categories = {
            "business", "entertainment", "general",
            "health", "science", "sports", "technology"
        }

    def top_headlines(self, category: str, page_size: int = 10) -> List[Dict[str, Any]]:
        # Check cache first
        cache_key = f"{self.cache_version}:th:{category}_{page_size}"
        if cache_key in self.cache:
            timestamp, data = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return data

        # Build parameters. For unsupported categories (e.g., world, politics),
        # use category=general and a keyword query to improve relevance.
        params: Dict[str, Any] = {
            "apiKey": self.api_key,
            "pageSize": page_size,
            "language": "en",
            "sortBy": "publishedAt",
            "country": "us",
        }
        cat = (category or "").lower()
        if cat in self.supported_categories:
            params["category"] = cat
        else:
            params["category"] = "general"
            params["q"] = cat if cat else "world"

        try:
            response = requests.get(
                f"{self.base_url}/top-headlines",
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "ok":
                raise Exception(data.get("message", "API request failed"))

            articles = data.get("articles", [])
            # Keep top headlines count stable for predefined topics; no strict filtering here

            # Fallback to /everything when top-headlines yields nothing (e.g., world/politics)
            if not articles:
                query_map = {
                    "world": "world OR international OR global",
                    "politics": "politics OR government OR election",
                    "science": "science OR research",
                    "health": "health OR medicine",
                    "sports": "sports OR game",
                }
                q = query_map.get(cat, cat or "world")
                ev_params = {
                    "apiKey": self.api_key,
                    "q": q,
                    "language": "en",
                    "pageSize": page_size,
                    "sortBy": "publishedAt"
                }
                try:
                    ev_resp = requests.get(f"{self.base_url}/everything", params=ev_params)
                    ev_resp.raise_for_status()
                    ev_data = ev_resp.json()
                    if ev_data.get("status") == "ok":
                        articles = ev_data.get("articles", [])
                except Exception as _:
                    pass
            
            # Cache the results
            self.cache[cache_key] = (datetime.now(), articles)
            
            return articles

        except Exception as e:
            print(f"News API error: {e}")
            return []

    def search(self, query: str, page_size: int = 10, days_back: int = 30) -> List[Dict[str, Any]]:
        """Free-text news search using the /everything endpoint.
        Applies a simple cache and relevance filter similar to top_headlines.
        """
        q = (query or '').strip()
        if not q:
            return []

        cache_key = f"{self.cache_version}:search:{q.lower()}::{page_size}"
        if cache_key in self.cache:
            timestamp, data = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_duration:
                return data

        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        # Build stronger boolean query for title-only search
        q_norm = q.lower().strip()
        terms = re.findall(r"[a-z0-9]+", q_norm)
        phrase = f'"{q_norm}"' if len(terms) > 1 else q_norm
        and_terms = " AND ".join(terms)
        boolean_q = f"{phrase} OR {and_terms}" if phrase and and_terms else (phrase or and_terms)
        fetch_size = min(100, max(page_size * 3, 30))

        params: Dict[str, Any] = {
            "apiKey": self.api_key,
            "q": boolean_q or q,
            "language": "en",
            "pageSize": fetch_size,
            "sortBy": "publishedAt",
            "from": from_date,
            "searchIn": "title",
        }

        try:
            response = requests.get(f"{self.base_url}/everything", params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "ok":
                raise Exception(data.get("message", "API request failed"))

            articles = data.get("articles", [])

            # Strict token-based filtering and ranking on titles
            key_words = set(terms)
            def _token_words(text: str) -> set:
                return set(re.findall(r"[a-z0-9]+", (text or "").lower()))
            def _relevant(a: Dict[str, Any]) -> bool:
                t_words = _token_words(a.get("title") or "")
                return key_words.issubset(t_words) if key_words else True
            def _score(a: Dict[str, Any]) -> int:
                t = (a.get("title") or "").lower()
                t_words = _token_words(t)
                exact = 10 if len(terms) > 1 and q_norm in t else 0
                hits = sum(1 for w in key_words if w in t_words)
                starts = 3 if len(terms) > 0 and t.startswith(q_norm) else 0
                return exact + hits * 2 + starts

            filtered = [a for a in articles if _relevant(a)]
            filtered.sort(key=_score, reverse=True)
            trimmed = filtered[:page_size] if page_size and page_size > 0 else filtered

            # Cache and return
            self.cache[cache_key] = (datetime.now(), trimmed)
            return trimmed
        except Exception as e:
            print(f"News API search error: {e}")
            return []