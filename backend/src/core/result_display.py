import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import networkx as nx
import io
import base64
import numpy as np

class Visualizer:
    def create_wordcloud(self, text):
        if not text:
            return ""
            
        try:
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='black',
                colormap='viridis'
            ).generate(text)
            
            img = io.BytesIO()
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.savefig(img, format='png', bbox_inches='tight', pad_inches=0)
            plt.close()
            
            return base64.b64encode(img.getvalue()).decode()
        except Exception as e:
            print(f"Wordcloud error: {e}")
            return ""

    def create_heatmap(self, data):
        try:
            # Reshape data into 2D matrix if needed
            matrix = np.array(data).reshape(-1, 1) if isinstance(data, list) else data
            
            fig = go.Figure(data=go.Heatmap(
                z=matrix,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(len=0.8)
            ))

            n = matrix.shape[0] if hasattr(matrix, 'shape') else len(data)
            fig.update_layout(
                title="Sentiment per Article",
                height=320,
                margin=dict(l=20, r=20, t=40, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    title="Articles",
                    showgrid=False, zeroline=False, visible=False
                ),
                yaxis=dict(
                    title="",
                    tickmode='array',
                    tickvals=list(range(n)),
                    ticktext=[str(i+1) for i in range(n)],
                    showgrid=False, zeroline=False
                )
            )

            return fig.to_json()
        except Exception as e:
            print(f"Heatmap error: {e}")
            return {}

    def create_network_graph(self, graph):
        try:
            # Keep top nodes by degree to reduce clutter
            deg = graph.degree()
            deg_sorted = sorted(deg, key=lambda x: x[1], reverse=True)
            keep_nodes = {n for n, _ in deg_sorted[:30]}
            H = graph.subgraph(keep_nodes).copy()

            pos = nx.spring_layout(H, k=0.5, seed=42)
            
            # Create edges trace
            edge_x, edge_y = [], []
            for edge in H.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

            edges_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines'
            )

            # Create nodes trace (hover text only to avoid clutter)
            node_x, node_y, node_text = [], [], []
            for node in H.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                node_text.append(str(node))

            nodes_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers',
                hoverinfo='text',
                text=node_text,
                marker=dict(
                    size=10,
                    color='#00bcd4',
                    line_width=2
                )
            )

            # Create figure
            fig = go.Figure(
                data=[edges_trace, nodes_trace],
                layout=go.Layout(
                    title='Content Relationship Network',
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=10,l=10,r=10,t=40),
                    height=320,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False)
                )
            )
            
            return fig.to_json()
        except Exception as e:
            print(f"Network graph error: {e}")
            return {}