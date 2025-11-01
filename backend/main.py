










import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
# Load environment variables
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

from src.core.news_fetcher import NewsFetcher
from src.core.pipeline import PipelineManager
from src.core.result_display import Visualizer
from src.core.content_extractor import clean_text

# Initialize components
fetcher = NewsFetcher(api_key=NEWS_API_KEY)
pipeline = PipelineManager()
visualizer = Visualizer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize resources
    print("Starting up NewsScope")
    yield
    # Shutdown: Clean up resources
    print("Shutting down NewsScope")

# Initialize FastAPI with lifespan
app = FastAPI(title="NewsScope", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Define path constants
BASE = Path(__file__).resolve().parent
FRONTEND = BASE.parent / "frontend"
STATIC = FRONTEND / "static"

# Verify paths exist
if not FRONTEND.exists() or not STATIC.exists():
    raise FileNotFoundError(f"Frontend directories not found at {FRONTEND}")

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

# ...rest of your existing routes...
TOPICS = [
    "business", "technology", "science", "health",
    "sports", "entertainment", "politics", "world"
]

# Define path constants
BASE = Path(__file__).resolve().parent
FRONTEND = BASE.parent / "frontend"
STATIC = FRONTEND / "static"

# Mount static files - this should come before route definitions
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")

# API Routes
@app.get("/")
async def serve_spa():
    index_path = FRONTEND / "index.html"
    if not index_path.exists():
        return JSONResponse(
            status_code=404,
            content={"message": "Frontend not found. Please check the frontend directory."}
        )
    return FileResponse(str(index_path))

# ... rest of your existing routes ...
# Keep all your existing route handlers (health, topics, topic_news, etc.)
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/topics")
def get_topics():
    return {"topics": TOPICS}

@app.get("/topic/{topic_name}")
async def topic_news(topic_name: str, page_size: int = 10):
    # Allow free-form topics; unknown ones will be handled by NewsFetcher
    
    try:
        # Get fresh news for the specific topic
        articles = fetcher.top_headlines(
            category=topic_name.lower(), 
            page_size=page_size
        )
        
        if not articles:
            return {
                "topic": topic_name,
                "articles": [],
                "message": "No news found for this topic"
            }

        processed_articles = []
        for article in articles:
            try:
                # Only process articles with content
                content = clean_text(
                    article.get("content") or 
                    article.get("description") or 
                    ""
                )
                if not content:
                    continue

                # Add timestamp to track article freshness
                article["timestamp"] = article.get("publishedAt")
                article["content"] = content
                article["analysis"] = pipeline.analyze_article(content, title=article.get("title"))
                processed_articles.append(article)
            except Exception as e:
                print(f"Article processing error: {e}")
                continue
                
        return {
            "topic": topic_name,
            "articles": processed_articles,
            "count": len(processed_articles),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching news: {str(e)}"
        )

@app.get("/search")
async def search_news(q: str, page_size: int = 10):
    """Free-text search endpoint: fetch articles for an arbitrary query and analyze them."""
    try:
        articles = fetcher.search(query=q, page_size=page_size)
        if not articles:
            return {"query": q, "articles": [], "count": 0, "message": "No news found for this query"}

        processed_articles = []
        for article in articles:
            try:
                content = clean_text(
                    article.get("content") or 
                    article.get("description") or 
                    ""
                )
                if not content:
                    continue

                article["timestamp"] = article.get("publishedAt")
                article["content"] = content
                article["analysis"] = pipeline.analyze_article(content, title=article.get("title"))
                processed_articles.append(article)
            except Exception as e:
                print(f"Search article processing error: {e}")
                continue

        return {
            "query": q,
            "articles": processed_articles,
            "count": len(processed_articles),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching news: {str(e)}")

@app.post("/summarize")
async def summarize(request: Request):
    try:
        data = await request.json()
        texts = data.get("texts", [])
        if not texts:
            raise HTTPException(status_code=400, detail="No texts provided")
            
        summaries = pipeline.summarize(texts)
        return {"summaries": summaries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/visualize/wordcloud")
async def create_wordcloud(request: Request):
    data = await request.json()
    texts = data.get("texts", [])
    combined_text = " ".join(texts)
    image = visualizer.create_wordcloud(combined_text)
    return {"image": image}

@app.post("/visualize/heatmap")
async def create_heatmap(request: Request):
    data = await request.json()
    articles = data.get("articles", [])
    sentiments = [a.get("analysis", {}).get("sentiment", {}).get("score", 0) for a in articles]
    heatmap_data = visualizer.create_heatmap(sentiments)
    return {"data": heatmap_data}

@app.post("/visualize/network")
async def create_network(request: Request):
    try:
        data = await request.json()
        articles = data.get("articles", [])
        
        if not articles:
            return {"data": {}}
            
        graph = pipeline.generate_content_graph(articles)
        network_data = visualizer.create_network_graph(graph)
        return {"data": network_data}
    except Exception as e:
        print(f"Network visualization error: {e}")
        raise HTTPException(status_code=500, detail="Error generating network visualization")
# Serve frontend
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/static/"):
        return JSONResponse(
            status_code=404,
            content={"message": f"Static file not found: {request.url.path}"}
        )
    return FileResponse(str(FRONTEND / "index.html"))