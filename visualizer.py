import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import json
import time
from pyvis.network import Network
import streamlit.components.v1 as components
from db import get_db_connection
from ai_explore import AIExplorer

def create_knowledge_graph(topic_data):
    """Create a NetworkX graph from topic data"""
    G = nx.Graph()
    
    # Add main topic node
    main_topic = topic_data["topic"]
    G.add_node(main_topic, size=25, color="#6200EA", title=topic_data["summary"])
    
    # Add related concepts
    for concept in topic_data.get("related_concepts", []):
        concept_name = concept["name"]
        G.add_node(concept_name, size=15, color="#7C4DFF", title=concept["summary"])
        G.add_edge(main_topic, concept_name, title=concept["relation"])
    
    # Add subtopics if they exist
    for subtopic in topic_data.get("subtopics", []):
        subtopic_name = subtopic["name"]
        G.add_node(subtopic_name, size=20, color="#3949AB", title=subtopic["summary"])
        G.add_edge(main_topic, subtopic_name, title="subtopic")
    
    return G

def convert_to_pyvis(nx_graph):
    """Convert NetworkX graph to PyVis for HTML visualization"""
    pyvis_net = Network(height="600px", width="100%", bgcolor="#FFFFFF", font_color="black")
    
    # Configure physics
    pyvis_net.barnes_hut(gravity=-5000, central_gravity=0.3, spring_length=150)
    
    # Add nodes and edges from NetworkX
    for node in nx_graph.nodes():
        node_attrs = nx_graph.nodes[node]
        pyvis_net.add_node(
            node, 
            label=node, 
            title=node_attrs.get("title", ""),
            size=node_attrs.get("size", 15),
            color=node_attrs.get("color", "#7C4DFF")
        )
    
    for edge in nx_graph.edges():
        edge_attrs = nx_graph.edges[edge]
        pyvis_net.add_edge(
            edge[0], 
            edge[1],
            title=edge_attrs.get("title", "")
        )
    
    return pyvis_net

def create_plotly_graph(nx_graph):
    """Create a Plotly visualization of the graph"""
    # Create positions for nodes using a spring layout
    pos = nx.spring_layout(nx_graph, seed=42)
    
    # Create edges
    edge_x = []
    edge_y = []
    edge_text = []
    
    for edge in nx_graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_text.append(nx_graph.edges[edge].get("title", ""))
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='#888'),
        hoverinfo='none',
        mode='lines')
    
    # Create nodes
    node_x = []
    node_y = []
    node_text = []
    node_size = []
    node_color = []
    
    for node in nx_graph.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node}<br>{nx_graph.nodes[node].get('title', '')}")
        node_size.append(nx_graph.nodes[node].get("size", 15))
        node_color.append(nx_graph.nodes[node].get("color", "#7C4DFF"))
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=False,
            color=node_color,
            size=node_size,
            line_width=2))
    
    # Create figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
    )
    
    return fig

def show_visualizer():
    """Main function to display the knowledge tree visualizer"""
    st.markdown("<h1 class='main-header'>🌳 Knowledge Tree Visualizer</h1>", unsafe_allow_html=True)
    
    # Initialize session state for visualizer
    if 'topic' not in st.session_state:
        st.session_state.topic = ""
    if 'topic_data' not in st.session_state:
        st.session_state.topic_data = None
    if 'graph' not in st.session_state:
        st.session_state.graph = None
    if 'visualization_type' not in st.session_state:
        st.session_state.visualization_type = "interactive"
    if 'exploration_depth' not in st.session_state:
        st.session_state.exploration_depth = 1
    if 'exploration_start_time' not in st.session_state:
        st.session_state.exploration_start_time = time.time()
    if 'nodes_explored' not in st.session_state:
        st.session_state.nodes_explored = set()
    if 'current_node' not in st.session_state:
        st.session_state.current_node = None
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### 🔍 Topic Explorer")
        
        # AI Provider selection
        ai_provider = st.selectbox(
            "AI Provider",
            ["Google Generative AI", "GROQ"],
            index=0
        )
        
        # Exploration depth
        exploration_depth = st.slider(
            "Exploration Depth",
            min_value=1,
            max_value=3,
            value=st.session_state.exploration_depth,
            help="Higher depth = more detailed information but slower response"
        )
        
        # Update session state if depth changed
        if exploration_depth != st.session_state.exploration_depth:
            st.session_state.exploration_depth = exploration_depth
        
        # Visualization type
        st.session_state.visualization_type = "interactive"
        
        # History of explored topics
        if st.session_state.authenticated:
            st.markdown("### 📚 Recent Topics")
            db = get_db_connection()
            recent_trees = db.get_knowledge_tree(st.session_state.user_id)[:5]
            
            for tree in recent_trees:
                if st.button(f"📌 {tree['topic']}", key=f"history_{tree['topic']}"):
                    st.session_state.topic = tree['topic']
                    st.session_state.topic_data = {
                        "topic": tree['topic'],
                        "summary": "Loaded from history",
                        "related_concepts": [],  # Will be populated from DB
                    }
                    
                    # Reconstruct topic data from saved nodes and edges
                    for node_id in tree['nodes']:
                        node = tree['nodes'][node_id]
                        if node_id != tree['topic']:  # Skip main topic node
                            concept = {
                                "name": node_id,
                                "summary": node.get('title', ''),
                                "relation": ""  # Will be filled from edges
                            }
                            st.session_state.topic_data["related_concepts"].append(concept)
                    
                    # Add relations from edges
                    for edge in tree['edges']:
                        for concept in st.session_state.topic_data["related_concepts"]:
                            if concept["name"] in edge:
                                concept["relation"] = tree['edges'][edge].get('title', '')
                    
                    # Set current node to main topic
                    st.session_state.current_node = tree['topic']
                    
                    # Update nodes explored
                    st.session_state.nodes_explored = set([tree['topic']])
                    
                    # Reset exploration time
                    st.session_state.exploration_start_time = time.time()
                    
                    st.rerun()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Topic input
        topic_input = st.text_input(
            "Enter a topic to explore",
            value=st.session_state.topic,
            help="Type any topic you want to learn about"
        )
        
        if topic_input != st.session_state.topic:
            st.session_state.topic = topic_input
        
        # Explore button
        if st.button("🔍 Explore Topic", disabled=not st.session_state.topic):
            with st.spinner(f"Exploring {st.session_state.topic}..."):
                # Initialize AI explorer with selected provider
                explorer = AIExplorer(
                    provider="google" if ai_provider == "Google Generative AI" else "groq"
                )
                
                # Get topic data
                st.session_state.topic_data = explorer.explore_topic(
                    st.session_state.topic,
                    depth=st.session_state.exploration_depth
                )
                
                # Create graph
                st.session_state.graph = create_knowledge_graph(st.session_state.topic_data)
                
                # Set current node to main topic
                st.session_state.current_node = st.session_state.topic
                
                # Update nodes explored
                st.session_state.nodes_explored.add(st.session_state.topic)
                
                # Reset exploration time
                st.session_state.exploration_start_time = time.time()
                
                # Save to database if authenticated
                if st.session_state.authenticated:
                    db = get_db_connection()
                    
                    # Convert NetworkX graph to node/edge dict for MongoDB
                    nodes_dict = {}
                    edges_dict = {}
                    
                    for node in st.session_state.graph.nodes():
                        nodes_dict[node] = dict(st.session_state.graph.nodes[node])
                    
                    for edge in st.session_state.graph.edges():
                        edge_key = f"{edge[0]}_{edge[1]}"
                        edges_dict[edge_key] = dict(st.session_state.graph.edges[edge])
                    
                    # Save to database
                    tree_id = db.save_knowledge_tree(
                        st.session_state.user_id,
                        st.session_state.topic,
                        nodes_dict,
                        edges_dict
                    )
        
        # Display visualization if graph exists
        if st.session_state.graph:
            st.markdown("### 🌳 Knowledge Tree")
            
            if st.session_state.visualization_type == "interactive":
                # Create PyVis visualization
                pyvis_net = convert_to_pyvis(st.session_state.graph)
                
                # Save and display HTML
                pyvis_net.save_graph("temp_graph.html")
                with open("temp_graph.html", "r", encoding="utf-8") as f:
                    html_data = f.read()
                
                # Display graph with custom height
                components.html(html_data, height=600)
    
    with col2:
        # Information panel
        st.markdown("### 📖 Topic Information")
        
        if st.session_state.topic_data:
            # Display current node information
            if st.session_state.current_node:
                # Get node information
                if st.session_state.current_node == st.session_state.topic_data["topic"]:
                    # Main topic
                    st.markdown(f"#### {st.session_state.current_node}")
                    st.markdown(st.session_state.topic_data["summary"])
                    
                    # Display key points if available
                    if "key_points" in st.session_state.topic_data:
                        st.markdown("#### Key Points")
                        for point in st.session_state.topic_data["key_points"]:
                            st.markdown(f"• {point}")
                else:
                    # Related concept
                    for concept in st.session_state.topic_data.get("related_concepts", []):
                        if concept["name"] == st.session_state.current_node:
                            st.markdown(f"#### {concept['name']}")
                            st.markdown(f"**Relation:** {concept['relation']}")
                            st.markdown(concept["summary"])
                            break
                    
                    # Check subtopics if not found in related concepts
                    if "subtopics" in st.session_state.topic_data:
                        for subtopic in st.session_state.topic_data["subtopics"]:
                            if subtopic["name"] == st.session_state.current_node:
                                st.markdown(f"#### {subtopic['name']}")
                                st.markdown(subtopic["summary"])
                                break
                
                # Get detailed explanation button
                if st.button("🔍 Get Detailed Explanation"):
                    with st.spinner(f"Getting details about {st.session_state.current_node}..."):
                        explorer = AIExplorer(
                            provider="google" if ai_provider == "Google Generative AI" else "groq"
                        )
                        explanation = explorer.get_detailed_explanation(st.session_state.current_node)
                        st.markdown(explanation)
                        
                        # Update nodes explored
                        st.session_state.nodes_explored.add(st.session_state.current_node)
            
            # Display related concepts for navigation
            st.markdown("### 🔄 Related Concepts")
            
            if "related_concepts" in st.session_state.topic_data:
                for concept in st.session_state.topic_data["related_concepts"]:
                    if st.button(f"📌 {concept['name']}", key=f"concept_{concept['name']}"):
                        st.session_state.current_node = concept["name"]
                        st.rerun()
            
            # Display subtopics if available
            if "subtopics" in st.session_state.topic_data:
                st.markdown("### 📑 Subtopics")
                
                for subtopic in st.session_state.topic_data["subtopics"]:
                    if st.button(f"📚 {subtopic['name']}", key=f"subtopic_{subtopic['name']}"):
                        st.session_state.current_node = subtopic["name"]
                        st.rerun()
            
            # Return to main topic button
            if st.session_state.current_node and st.session_state.current_node != st.session_state.topic_data["topic"]:
                if st.button(f"🔙 Back to {st.session_state.topic_data['topic']}"):
                    st.session_state.current_node = st.session_state.topic_data["topic"]
                    st.rerun()
    
    # If user is authenticated, log session when they leave
    if st.session_state.authenticated and st.session_state.topic_data:
        # Check if we need to log the session
        current_time = time.time()
        time_spent = current_time - st.session_state.exploration_start_time
        
        # Log session after 30 seconds of exploration
        if time_spent > 30 and len(st.session_state.nodes_explored) > 0:
            db = get_db_connection()
            
            # Get tree ID
            tree = db.get_knowledge_tree(st.session_state.user_id, st.session_state.topic)
            tree_id = str(tree["_id"]) if tree else None
            
            if tree_id:
                # Log session
                db.log_learning_session(
                    st.session_state.user_id,
                    st.session_state.topic,
                    tree_id,
                    list(st.session_state.nodes_explored),
                    int(time_spent)
                )
                
                # Reset timer
                st.session_state.exploration_start_time = current_time
