import re
import string
import json
import networkx as nx
import base64
import datetime
import streamlit as st

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        encoded = base64.b64encode(img_file.read()).decode()
    return f"data:image/png;base64,{encoded}"


def clean_text(text):
    """Clean and normalize text for better processing"""
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation except hyphens
    exclude = set(string.punctuation.replace('-', ''))
    text = ''.join(ch for ch in text if ch not in exclude)
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def format_topic(topic):
    """Format topic string for display (capitalize words)"""
    return ' '.join(word.capitalize() for word in topic.split())

def truncate_text(text, max_length=100):
    """Truncate text to maximum length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def safe_json_loads(json_str):
    """Safely load JSON with error handling"""
    try:
        return json.loads(json_str)
    except Exception as e:
        st.error(f"Error parsing JSON: {e}")
        return {}

def networkx_to_nodes_edges(graph):
    """Convert NetworkX graph to nodes and edges dictionaries for DB storage"""
    nodes = {}
    edges = {}
    
    # Convert nodes
    for node in graph.nodes():
        nodes[node] = dict(graph.nodes[node])
    
    # Convert edges
    for edge in graph.edges():
        edge_key = f"{edge[0]}_{edge[1]}"
        edges[edge_key] = dict(graph.edges[edge])
    
    return nodes, edges

def nodes_edges_to_networkx(nodes, edges):
    """Convert nodes and edges dictionaries to NetworkX graph"""
    G = nx.Graph()
    
    # Add nodes
    for node_id, node_attrs in nodes.items():
        G.add_node(node_id, **node_attrs)
    
    # Add edges
    for edge_key, edge_attrs in edges.items():
        source, target = edge_key.split('_')
        G.add_edge(source, target, **edge_attrs)
    
    return G

def estimate_reading_time(text, words_per_minute=200):
    """Estimate reading time in minutes based on word count"""
    word_count = len(text.split())
    minutes = word_count / words_per_minute
    return max(1, round(minutes))

def format_datetime(dt):
    """Format datetime for display"""