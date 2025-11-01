const API_BASE = "http://127.0.0.1:8000";

const topicIcons = {
    technology: '💻',
    business: '💼',
    science: '🔬',
    health: '🏥',
    sports: '⚽',
    entertainment: '🎬',
    politics: '🏛️',
    world: '🌍'
};


async function loadTopics() {
    try {
        const res = await fetch(`${API_BASE}/topics`);
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        const data = await res.json();
        const topics = data.topics || [];
        
        if (topics.length === 0) {
            throw new Error("No topics received");
        }
        
        document.getElementById('topicGrid').innerHTML = topics.map(topic => `
            <div class="topic-card" onclick="showTopicNews('${topic}')">
                <div class="topic-icon">${topicIcons[topic] || '📰'}</div>
                <h3 class="topic-title">${topic.charAt(0).toUpperCase() + topic.slice(1)}</h3>
            </div>
        `).join('');
    } catch (err) {
        console.error("Error loading topics:", err);
        document.getElementById('topicGrid').innerHTML = `
            <div class="error-message">Failed to load topics. Please try again later.</div>
        `;
    }
}

async function showTopicNews(topic) {
    const modalContent = document.getElementById('modalContent');
    modalContent.innerHTML = `
        <h2>${topic.charAt(0).toUpperCase() + topic.slice(1)} News</h2>
        <div class="loading">Fetching latest news and generating insights...</div>
        <div class="visualization-grid">
            <div class="vis-card" id="wordcloud">
                <h3>Topic Keywords</h3>
            </div>
            <div class="vis-card" id="heatmap">
                <h3>Sentiment Analysis</h3>
            </div>
            <div class="vis-card" id="network">
                <h3>Content Relationships</h3>
            </div>
        </div>
        <div class="news-grid" id="newsGrid"></div>
    `;
    
    showModal();

    try {
        const res = await fetch(`${API_BASE}/topic/${encodeURIComponent(topic)}`);
        const data = await res.json();
        const articles = data.articles || [];

        if (articles.length === 0) {
            modalContent.innerHTML = `
                <h2>${topic.charAt(0).toUpperCase() + topic.slice(1)} News</h2>
                <p>No news found for this topic.</p>
            `;
            return;
        }

        // Generate visualizations
        await Promise.all([
            generateWordCloud(articles),
            generateHeatmap(articles),
            generateNetwork(articles)
        ]);

        // Display articles
        document.getElementById('newsGrid').innerHTML = articles.map(article => `
            <div class="news-card">
                <h3>${article.title}</h3>
                <p>${article.analysis?.summary || article.description || ''}</p>
                <div class="article-meta">
                    <span class="sentiment ${getSentimentClass(article.analysis?.sentiment)}">
                        ${article.analysis?.sentiment?.label || 'Neutral'}
                    </span>
                    ${renderCategory(article.analysis?.category)}
                    <div class="entities">
                        ${formatEntities(article.analysis?.entities || [])}
                    </div>
                </div>
                <a href="${article.url}" target="_blank" class="read-more">Read More →</a>
            </div>
        `).join('');

    } catch (err) {
        console.error("Error:", err);
        modalContent.innerHTML = `
            <h2>${topic.charAt(0).toUpperCase() + topic.slice(1)} News</h2>
            <p class="error-message">Error loading news. Please try again later.</p>
        `;
    }
}

async function generateWordCloud(articles) {
    try {
        const res = await fetch(`${API_BASE}/visualize/wordcloud`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                texts: articles.map(a => a.content)
            })
        });
        const data = await res.json();
        const wc = document.getElementById('wordcloud');
        // Remove any previous image first
        const oldImg = wc.querySelector('img');
        if (oldImg) oldImg.remove();
        const img = document.createElement('img');
        img.src = `data:image/png;base64,${data.image}`;
        img.alt = 'Word Cloud';
        img.style.width = '100%';
        img.style.height = 'auto';
        img.style.display = 'block';
        wc.appendChild(img);
    } catch (err) {
        console.error("Wordcloud error:", err);
    }
}

async function generateHeatmap(articles) {
    try {
        const res = await fetch(`${API_BASE}/visualize/heatmap`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ articles })
        });
        const data = await res.json();
        const fig = JSON.parse(data.data);
        Plotly.newPlot('heatmap', fig.data, fig.layout, {displayModeBar: false, responsive: true});
    } catch (err) {
        console.error("Heatmap error:", err);
    }
}

async function generateNetwork(articles) {
    try {
        const res = await fetch(`${API_BASE}/visualize/network`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ articles })
        });
        const data = await res.json();
        const fig = JSON.parse(data.data);
        Plotly.newPlot('network', fig.data, fig.layout, {displayModeBar: false, responsive: true});
    } catch (err) {
        console.error("Network graph error:", err);
    }
}

function getSentimentClass(sentiment) {
    if (!sentiment) return 'neutral';
    const score = sentiment.score || 0;
    if (score > 0.3) return 'positive';
    if (score < -0.3) return 'negative';
    return 'neutral';
}

function formatEntities(entities) {
    if (!Array.isArray(entities)) return '';
    return entities
        .slice(0, 3)
        .map(e => {
            // Support either array or object shape
            if (e && typeof e === 'object') {
                const text = e.text || (Array.isArray(e) ? e[0] : '') || '';
                return `<span class="entity">${text}</span>`;
            }
            if (Array.isArray(e)) {
                return `<span class="entity">${e[0] || ''}</span>`;
            }
            return '';
        })
        .join('');
}

function showModal() {
    document.getElementById('newsModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('newsModal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target === document.getElementById('newsModal')) {
        closeModal();
    }
}

// Initialize on page load
window.onload = loadTopics;

// --- Search support ---
function handleSearch(e) {
    e.preventDefault();
    const q = (document.getElementById('searchInput').value || '').trim();
    if (!q) return false;
    showSearch(q);
    return false;
}

async function showSearch(query) {
    const modalContent = document.getElementById('modalContent');
    modalContent.innerHTML = `
        <h2>Results for "${query}"</h2>
        <div class="loading">Fetching latest news and generating insights...</div>
        <div class="visualization-grid">
            <div class="vis-card" id="wordcloud">
                <h3>Topic Keywords</h3>
            </div>
            <div class="vis-card" id="heatmap">
                <h3>Sentiment Analysis</h3>
            </div>
            <div class="vis-card" id="network">
                <h3>Content Relationships</h3>
            </div>
        </div>
        <div class="news-grid" id="newsGrid"></div>
    `;
    showModal();

    try {
        const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        const articles = data.articles || [];

        if (articles.length === 0) {
            modalContent.innerHTML = `
                <h2>Results for "${query}"</h2>
                <p>No news found for this query.</p>
            `;
            return;
        }

        await Promise.all([
            generateWordCloud(articles),
            generateHeatmap(articles),
            generateNetwork(articles)
        ]);

        document.getElementById('newsGrid').innerHTML = articles.map(article => `
            <div class="news-card">
                <h3>${article.title}</h3>
                <p>${article.analysis?.summary || article.description || ''}</p>
                <div class="article-meta">
                    <span class="sentiment ${getSentimentClass(article.analysis?.sentiment)}">
                        ${article.analysis?.sentiment?.label || 'Neutral'}
                    </span>
                    ${renderCategory(article.analysis?.category)}
                    <div class="entities">
                        ${formatEntities(article.analysis?.entities || [])}
                    </div>
                </div>
                <a href="${article.url}" target="_blank" class="read-more">Read More →</a>
            </div>
        `).join('');

    } catch (err) {
        console.error("Search error:", err);
        modalContent.innerHTML = `
            <h2>Results for "${query}"</h2>
            <p class="error-message">Error loading news. Please try again later.</p>
        `;
    }
}

function renderCategory(cat) {
    if (!cat || !cat.label) return '';
    const label = String(cat.label).trim();
    if (!label) return '';
    return `<span class="category-badge">${label}</span>`;
}