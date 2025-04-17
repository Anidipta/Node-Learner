import streamlit as st
import networkx as nx
import pyvis.network as net
import tempfile
import os
import time
import json
from datetime import datetime
from db import store_session, get_session_by_id
from ai_explainer import get_ai_explanation, get_youtube_links
import base64
import pdfkit
from streamlit_extras.switch_page_button import switch_page

# Color scheme
THEME = {
    "background": "#121212",
    "primary": "#BB86FC",
    "secondary": "#03DAC6",
    "error": "#CF6679",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B3B3B3",
    "node_colors": {
        "root": "#BB86FC",
        "branch": "#3700B3",
        "leaf": "#6200EE",
        "highlighted": "#CF6679"
    }
}

class KnowledgeTree:
    def __init__(self, root_topic=None):
        self.G = nx.DiGraph()
        self.start_time = time.time()
        self.topic_times = {}
        self.current_topic = None
        self.topic_start_time = None
        
        if root_topic:
            self.G.add_node(root_topic, level=0, color=THEME["node_colors"]["root"], size=25)
            self.current_topic = root_topic
            self.topic_start_time = time.time()
            self.topic_times[root_topic] = 0
    
    def add_node(self, parent, child, level=None):
        if level is None:
            parent_level = self.G.nodes[parent].get('level', 0)
            level = parent_level + 1
        
        node_color = THEME["node_colors"]["branch"] if level < 3 else THEME["node_colors"]["leaf"]
        
        self.G.add_node(child, level=level, color=node_color, size=20)
        self.G.add_edge(parent, child)
        return child
    
    def switch_topic(self, new_topic):
        if self.current_topic:
            elapsed = time.time() - self.topic_start_time
            self.topic_times[self.current_topic] = self.topic_times.get(self.current_topic, 0) + elapsed
        
        self.current_topic = new_topic
        self.topic_start_time = time.time()
        if new_topic not in self.topic_times:
            self.topic_times[new_topic] = 0
    
    def get_total_time(self):
        # Update time for current topic
        if self.current_topic:
            elapsed = time.time() - self.topic_start_time
            current_total = self.topic_times.get(self.current_topic, 0) + elapsed
            return sum([time for topic, time in self.topic_times.items() if topic != self.current_topic], current_total)
        return sum(self.topic_times.values())
    
    def get_topic_time(self, topic):
        if topic == self.current_topic:
            elapsed = time.time() - self.topic_start_time
            return self.topic_times.get(topic, 0) + elapsed
        return self.topic_times.get(topic, 0)
    
    def remove_node(self, node):
        children = list(self.G.successors(node))
        for child in children:
            self.remove_node(child)
        
        self.G.remove_node(node)
        if node in self.topic_times:
            del self.topic_times[node]
        
        if node == self.current_topic:
            self.current_topic = None
            self.topic_start_time = None
    
    def get_visualization(self):
        nt = net.Network(height="600px", width="100%", bgcolor=THEME["background"], 
                        font_color=THEME["text_primary"])
        
        # Copy the graph to avoid modifying the original
        temp_graph = self.G.copy()
        
        # Add all nodes and edges to the pyvis network
        for node, attrs in temp_graph.nodes(data=True):
            nt.add_node(node, 
                      label=node, 
                      color=attrs.get('color', THEME["node_colors"]["leaf"]),
                      size=attrs.get('size', 15),
                      title=f"Time: {format_time(self.get_topic_time(node))}")
        
        for edge in temp_graph.edges():
            nt.add_edge(edge[0], edge[1], color=THEME["secondary"])
        
        # Set physics options for better visualization
        nt.set_options("""
        var options = {
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -50,
                    "centralGravity": 0.01,
                    "springLength": 100,
                    "springConstant": 0.08
                },
                "maxVelocity": 50,
                "solver": "forceAtlas2Based",
                "timestep": 0.35,
                "stabilization": {
                    "enabled": true,
                    "iterations": 1000
                }
            }
        }
        """)
        
        # Create a temporary file to save the HTML
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp:
            path = tmp.name
            nt.save_graph(path)
        
        return path
    
    def export_data(self):
        data = {
            "nodes": list(self.G.nodes()),
            "edges": list(self.G.edges()),
            "topic_times": {k: round(v, 2) for k, v in self.topic_times.items()},
            "total_time": round(self.get_total_time(), 2),
            "created_at": datetime.now().isoformat()
        }
        return data
    
    def generate_summary_html(self, ai_explanations=None):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>NodeLearn Session Summary</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: {THEME["background"]}; color: {THEME["text_primary"]}; }}
                h1, h2, h3 {{ color: {THEME["primary"]}; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .stats {{ display: flex; justify-content: space-between; margin: 20px 0; }}
                .stat-box {{ background-color: #1E1E1E; padding: 15px; border-radius: 5px; width: 30%; text-align: center; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: {THEME["secondary"]}; }}
                .topic {{ margin-bottom: 15px; padding: 10px; background-color: #1E1E1E; border-radius: 5px; }}
                .topic-header {{ display: flex; justify-content: space-between; align-items: center; }}
                .topic-name {{ font-weight: bold; color: {THEME["primary"]}; }}
                .topic-time {{ color: {THEME["text_secondary"]}; }}
                .topic-content {{ margin-top: 10px; }}
                .subtopics {{ margin-left: 20px; }}
                footer {{ margin-top: 30px; text-align: center; color: {THEME["text_secondary"]}; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>NodeLearn Session Summary</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-value">{len(self.G.nodes())}</div>
                        <div>Topics Explored</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{format_time(self.get_total_time())}</div>
                        <div>Total Time</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{len(self.G.edges())}</div>
                        <div>Connections Made</div>
                    </div>
                </div>
                
                <h2>Knowledge Tree</h2>
        """
        
        # Add topic information
        for node in self.G.nodes():
            level = self.G.nodes[node].get('level', 0)
            parent_list = list(self.G.predecessors(node))
            parent = parent_list[0] if parent_list else None
            
            # Only process root nodes or direct children in this loop
            if level == 0:
                html += f"""
                <div class="topic">
                    <div class="topic-header">
                        <span class="topic-name">{node}</span>
                        <span class="topic-time">{format_time(self.get_topic_time(node))}</span>
                    </div>
                """
                
                # Add AI explanation if available
                if ai_explanations and node in ai_explanations:
                    html += f"""
                    <div class="topic-content">
                        <p>{ai_explanations[node]['explanation']}</p>
                    """
                    
                    # Add links if available
                    if 'links' in ai_explanations[node] and ai_explanations[node]['links']:
                        html += "<p><strong>Recommended Resources:</strong></p><ul>"
                        for link in ai_explanations[node]['links']:
                            html += f"<li><a href='{link['url']}'>{link['title']}</a></li>"
                        html += "</ul>"
                    
                    html += "</div>"
                
                # Add subtopics
                children = list(self.G.successors(node))
                if children:
                    html += "<div class='subtopics'>"
                    for child in children:
                        child_time = format_time(self.get_topic_time(child))
                        html += f"""
                        <div class="topic">
                            <div class="topic-header">
                                <span class="topic-name">{child}</span>
                                <span class="topic-time">{child_time}</span>
                            </div>
                        """
                        
                        # Add AI explanation for child if available
                        if ai_explanations and child in ai_explanations:
                            html += f"""
                            <div class="topic-content">
                                <p>{ai_explanations[child]['explanation']}</p>
                            """
                            
                            # Add links if available
                            if 'links' in ai_explanations[child] and ai_explanations[child]['links']:
                                html += "<p><strong>Recommended Resources:</strong></p><ul>"
                                for link in ai_explanations[child]['links']:
                                    html += f"<li><a href='{link['url']}'>{link['title']}</a></li>"
                                html += "</ul>"
                            
                            html += "</div>"
                        
                        # Add grandchildren summary
                        grandchildren = list(self.G.successors(child))
                        if grandchildren:
                            html += f"<div class='subtopics'><p>Subtopics: {', '.join(grandchildren)}</p></div>"
                        
                        html += "</div>"
                    html += "</div>"
                
                html += "</div>"
        
        html += """
                <footer>
                    <p>Created with NodeLearn - Interactive Knowledge Exploration Tool</p>
                </footer>
            </div>
        </body>
        </html>
        """
        
        return html

def format_time(seconds):
    """Format seconds into a readable time string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def generate_pdf_from_html(html_content):
    """Generate a PDF file from HTML content."""
    pdf_path = os.path.join(tempfile.gettempdir(), f"nodelearn_{int(time.time())}.pdf")
    
    try:
        pdfkit.from_string(html_content, pdf_path)
        return pdf_path
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

def get_pdf_download_link(pdf_path, filename="nodelearn_summary.pdf"):
    """Generate a download link for a PDF file."""
    with open(pdf_path, "rb") as file:
        pdf_bytes = file.read()
    
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download Session Summary PDF</a>'
    return href

def show_visualizer():
    st.title("🧠 NodeLearn - Interactive Knowledge Tree")
    
    # Set up session state
    if 'knowledge_tree' not in st.session_state:
        st.session_state.knowledge_tree = None
    if 'ai_explanations' not in st.session_state:
        st.session_state.ai_explanations = {}
    if 'current_topic' not in st.session_state:
        st.session_state.current_topic = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    
    # Configuration sidebar
    with st.sidebar:
        st.subheader("🛠️ Configuration")
        
        # AI Explanation Level
        ai_level = st.select_slider(
            "AI Explanation Detail Level",
            options=["Basic", "Intermediate", "Advanced", "Expert"],
            value="Intermediate"
        )
        
        st.divider()
        
        # Session stats if tree exists
        if st.session_state.knowledge_tree:
            st.subheader("📊 Session Stats")
            st.write(f"**Topics Explored:** {len(st.session_state.knowledge_tree.G.nodes())}")
            st.write(f"**Connections Made:** {len(st.session_state.knowledge_tree.G.edges())}")
            st.write(f"**Time Spent:** {format_time(st.session_state.knowledge_tree.get_total_time())}")
            
            # Exit and save button
            if st.button("🚪 Exit & Save Session", type="primary"):
                # Generate session summary and save
                ai_explanations = st.session_state.ai_explanations
                html_content = st.session_state.knowledge_tree.generate_summary_html(ai_explanations)
                
                # Generate PDF
                pdf_path = generate_pdf_from_html(html_content)
                
                # Save to MongoDB
                session_data = st.session_state.knowledge_tree.export_data()
                session_data['ai_explanations'] = ai_explanations
                session_data['detail_level'] = ai_level
                
                if pdf_path:
                    with open(pdf_path, "rb") as pdf_file:
                        pdf_binary = pdf_file.read()
                    session_data['pdf'] = Binary(pdf_binary)
                
                session_id = store_session(session_data)
                st.session_state.session_id = session_id
                
                # Show success message and provide link to history
                st.success("Session saved successfully!")
                st.markdown(get_pdf_download_link(pdf_path), unsafe_allow_html=True)
                
                # Clear session state
                st.session_state.knowledge_tree = None
                st.session_state.ai_explanations = {}
                st.session_state.current_topic = None
                
                # Redirect to history page
                switch_page("history")
    
    # Main content area
    if not st.session_state.knowledge_tree:
        st.write("Start exploring knowledge by entering a root topic.")
        root_topic = st.text_input("Root Topic")
        
        if st.button("Start Exploration", type="primary"):
            if root_topic:
                st.session_state.knowledge_tree = KnowledgeTree(root_topic)
                st.session_state.current_topic = root_topic
                
                # Get AI explanation for root topic
                explanation = get_ai_explanation(root_topic, ai_level)
                links = get_youtube_links(root_topic)
                st.session_state.ai_explanations[root_topic] = {
                    "explanation": explanation,
                    "links": links
                }
                
                st.rerun()
            else:
                st.error("Please enter a root topic to start.")
    else:
        # Two-column layout
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # Display the network visualization
            html_path = st.session_state.knowledge_tree.get_visualization()
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            st.components.v1.html(html_content, height=600)
            
            # Clean up the temporary file
            try:
                os.unlink(html_path)
            except:
                pass
        
        with col2:
            # Interactive panel for the current node
            current_topic = st.session_state.current_topic
            st.subheader(f"🔍 Current Topic: {current_topic}")
            
            # Topic actions
            st.write(f"Time spent: {format_time(st.session_state.knowledge_tree.get_topic_time(current_topic))}")
            
            # Show AI explanation
            with st.expander("🧠 AI Explanation", expanded=True):
                if current_topic in st.session_state.ai_explanations:
                    st.write(st.session_state.ai_explanations[current_topic]['explanation'])
                    
                    # Show resource links
                    if 'links' in st.session_state.ai_explanations[current_topic] and st.session_state.ai_explanations[current_topic]['links']:
                        st.subheader("📚 Resources")
                        for link in st.session_state.ai_explanations[current_topic]['links']:
                            st.markdown(f"[{link['title']}]({link['url']})")
                else:
                    with st.spinner("Generating AI explanation..."):
                        explanation = get_ai_explanation(current_topic, ai_level)
                        links = get_youtube_links(current_topic)
                        st.session_state.ai_explanations[current_topic] = {
                            "explanation": explanation,
                            "links": links
                        }
                    st.rerun()
            
            # Add subtopic
            with st.expander("➕ Add Subtopic"):
                new_topic = st.text_input("New subtopic name", key="new_topic")
                if st.button("Add", key="add_subtopic"):
                    if new_topic and new_topic not in st.session_state.knowledge_tree.G.nodes():
                        child = st.session_state.knowledge_tree.add_node(current_topic, new_topic)
                        st.session_state.current_topic = new_topic
                        st.session_state.knowledge_tree.switch_topic(new_topic)
                        
                        # Get AI explanation for new topic
                        with st.spinner("Generating AI explanation..."):
                            explanation = get_ai_explanation(new_topic, ai_level)
                            links = get_youtube_links(new_topic)
                            st.session_state.ai_explanations[new_topic] = {
                                "explanation": explanation,
                                "links": links
                            }
                        
                        st.rerun()
                    elif new_topic in st.session_state.knowledge_tree.G.nodes():
                        st.error("This topic already exists in your knowledge tree.")
                    else:
                        st.error("Please enter a valid topic name.")
            
            # Navigate to different node or delete current node
            with st.expander("🧭 Navigate"):
                # Get available nodes
                nodes = list(st.session_state.knowledge_tree.G.nodes())
                
                selected_node = st.selectbox("Select a node to navigate to", nodes)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Go to Node"):
                        st.session_state.current_topic = selected_node
                        st.session_state.knowledge_tree.switch_topic(selected_node)
                        st.rerun()
                
                with col2:
                    if st.button("Delete Current Node", type="secondary"):
                        # Only allow deletion if it's not the root node and has no children
                        if len(list(st.session_state.knowledge_tree.G.predecessors(current_topic))) > 0:
                            # Get parent node
                            parent = list(st.session_state.knowledge_tree.G.predecessors(current_topic))[0]
                            
                            # Remove the current node
                            st.session_state.knowledge_tree.remove_node(current_topic)
                            
                            # Switch to parent node
                            st.session_state.current_topic = parent
                            st.session_state.knowledge_tree.switch_topic(parent)
                            
                            st.rerun()
                        else:
                            st.error("Cannot delete the root node.")
