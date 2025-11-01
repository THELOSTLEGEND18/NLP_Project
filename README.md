# NewsScope

An intelligent news analysis platform powered by AI that helps you discover, read, and understand news articles with automated insights and visualizations.

## 🌟 Features

- **Smart News Search**: Search for any topic with intelligent filtering that shows only highly relevant articles
- **Predefined Topics**: Quick access to popular news categories (Business, Sports, Health, Technology, etc.)
- **AI-Powered Summaries**: Automatically generates concise summaries of lengthy articles using DistilBART
- **Sentiment Analysis**: Identifies whether articles are Positive, Negative, or Neutral
- **Named Entity Recognition**: Extracts key people, organizations, and locations from articles
- **Keyword Extraction**: Highlights the main topics discussed in each article
- **Interactive Visualizations**:
  - Word Cloud: Shows most frequently used words
  - Sentiment Heatmap: Visual representation of overall news sentiment
  - Network Graph: Displays connections between topics and entities

## 🛠️ Tech Stack

### Frontend
- **HTML/CSS/JavaScript**: Core web technologies
- **Plotly.js**: Interactive data visualizations

### Backend
- **Python 3.11**: Programming language
- **FastAPI**: Modern, fast web framework
- **Uvicorn**: ASGI web server

### AI/ML Libraries
- **Transformers (Hugging Face)**: NLP models
- **DistilBART**: Text summarization
- **spaCy**: Named entity recognition
- **NLTK**: Sentiment analysis and keyword extraction
- **PyTorch**: Deep learning framework

### Data Source
- **NewsAPI**: Real-time news from thousands of sources worldwide

## 📋 Prerequisites

- Python 3.11 or higher
- NewsAPI Key (Get free at https://newsapi.org/)
- Git (for cloning the repository)

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/THELOSTLEGEND18/NLP_Project.git
cd NLP_Project
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Download spaCy Model
```bash
python -m spacy download en_core_web_sm
```

### 5. Set Up Environment Variables
Create a `.env` file in the `backend` directory:
```bash
NEWS_API_KEY=your_newsapi_key_here
```

**Get your free NewsAPI key:** https://newsapi.org/register

### 6. Run the Application

#### Start the Backend Server

Windows (PowerShell): run in the current window
```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Windows (PowerShell): start in a new window (recommended on Windows)
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $((Resolve-Path backend).Path); & ..\\.venv\\Scripts\\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000"
```

Notes for Windows:
- Avoid using `--reload` (file-watcher) as it can cause shutdowns on Windows.
- If the server still exits immediately, try disabling lifespan events:
```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --no-lifespan
```

macOS/Linux:
```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

#### Access the Application
Open your browser and go to:
```
http://127.0.0.1:8000
```

## 📖 How to Use

1. **Search for News**: 
   - Type any topic in the search bar (e.g., "cricket", "technology", "elections")
   - Press Enter or click the search button

2. **Browse Topics**: 
   - Click on predefined topic buttons (Business, Sports, Health, etc.)

3. **View Results**:
   - Read AI-generated summaries
   - Check sentiment badges (Positive/Negative/Neutral)
   - Explore interactive visualizations
   - Click "Read More" to view full articles

## 📁 Project Structure

```
NLP_Project/
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── requirements.txt           # Python dependencies
│   └── src/
│       ├── core/
│       │   ├── news_fetcher.py    # NewsAPI integration
│       │   ├── pipeline.py        # NLP analysis pipeline
│       │   ├── summarizer.py      # Text summarization
│       │   ├── content_extractor.py
│       │   ├── result_display.py
│       │   ├── topic_classifier.py
│       │   └── topic_clusterer.py
│       └── utils/
├── frontend/
│   ├── index.html                 # Main HTML file
│   └── static/
│       ├── app.js                 # Frontend JavaScript
│       └── styles.css             # Styling
├── .gitignore
└── README.md
```

## 🔧 Configuration

### Search Behavior
- **Search Bar**: Returns only articles where ALL query words appear in the title (strict matching)
- **Predefined Topics**: Always returns up to 10 articles

### Cache Settings
- Results are cached for 15 minutes to improve performance
- Cache is automatically invalidated when search logic changes

## 🎯 API Endpoints

- `GET /` - Serves the frontend application
- `GET /health` - Health check endpoint
- `GET /topics` - Returns list of available topics
- `GET /topic/{topic_name}` - Fetches news for a specific topic
- `GET /search?q={query}` - Searches news by keyword
- `POST /summarize` - Generates summaries for provided texts
- `POST /visualize/wordcloud` - Creates word cloud data
- `POST /visualize/heatmap` - Creates sentiment heatmap data
- `POST /visualize/network` - Creates network graph data

## 🧠 AI Models Used

1. **sshleifer/distilbart-cnn-12-6** - Abstractive text summarization
2. **en_core_web_sm** - spaCy model for NER and text processing
3. **NLTK VADER** - Sentiment analysis
4. **NLTK** - Keyword extraction

## 🧪 NLP Topics Used

- **Text Cleaning & Normalization**: basic HTML/whitespace cleanup and lowercasing for consistent analysis
- **Abstractive Summarization**: generates human-like summaries of articles (DistilBART)
- **Extractive Summarization (TextRank-style)**: fallback summary using sentence similarity + PageRank
- **Named Entity Recognition (NER)**: detects people, organizations, locations (spaCy)
- **Sentiment Analysis**: classifies article tone as Positive/Negative/Neutral (VADER)
- **Keyword Extraction**: simple frequency-based keywords for quick topic cues
- **Topic Classification (title-based, optional)**: predicts a category from the article title (T5 model when available)
- **Topic Clustering**: groups related articles using embeddings or TF‑IDF + KMeans
- **Entity Network Graph**: builds connections between articles and entities for relationship visualization

## 🐛 Troubleshooting

### Server won't start
- Make sure virtual environment is activated
- Check if port 8000 is already in use
- Verify all dependencies are installed: `pip install -r backend/requirements.txt`

### No news results
- Verify your NewsAPI key is correct in `.env`
- Check your internet connection
- NewsAPI free tier has rate limits (100 requests/day)

### Models not loading
- First run will download AI models (may take a few minutes)
- Ensure you have sufficient disk space (~500MB for models)
- Run: `python -m spacy download en_core_web_sm`

## 📝 License

This project is for educational purposes.

## 👥 Contributors

- THELOSTLEGEND18

## 🙏 Acknowledgments

- NewsAPI for providing news data
- Hugging Face for transformer models
- spaCy for NLP capabilities
- Plotly for visualization tools

## 📷 Screenshots

Drop screenshots into `frontend/static/visuals/` and they will render here. Suggested captures:

- Home/Search view
- Topic results (e.g., Sports)
- Article card (summary + sentiment badge + entities)
- Visualizations: Word Cloud, Sentiment Heatmap, Network Graph

Example (replace filenames with your own):

![Home](frontend/static/visuals/home.png)
![Topic Results](frontend/static/visuals/topic_sports.png)
![Article Card](frontend/static/visuals/article_card.png)
![Word Cloud](frontend/static/visuals/wordcloud.png)
![Sentiment Heatmap](frontend/static/visuals/heatmap.png)
![Entity Network](frontend/static/visuals/network.png)

Tips:
- Use 1366×768 or 1920×1080 resolution for crisp images
- Keep filenames lowercase, hyphenated or underscored
- Commit screenshots to the repo so they render on GitHub

## 🗺️ Architecture Diagram

Mermaid (renders on GitHub):

```mermaid
flowchart TD
      U[User in Browser] --> F[Frontend (HTML/CSS/JS + Plotly)]
      F -->|HTTP/JSON| B[FastAPI Backend]
      B -->|Fetch| N[(NewsAPI)]
      B --> P[AI/NLP Pipeline]
      P -->|Summaries| B
      P -->|Sentiment/NER/Keywords| B
      B --> F

      subgraph Backend
         B
         P
      end
```

ASCII alternative:

```
User → Frontend (HTML/CSS/JS, Plotly)
         → FastAPI Backend (Uvicorn)
            → NewsFetcher → NewsAPI
            → NLP Pipeline → Summarizer (DistilBART), NER (spaCy), Sentiment (VADER), Keywords, Clustering
         → Frontend Visualizations (Word Cloud, Heatmap, Network)
```
