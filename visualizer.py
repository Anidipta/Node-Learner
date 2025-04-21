import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import json
import time
import uuid
from pyvis.network import Network
import streamlit.components.v1 as components
from db import get_db_connection
from ai_explainer import AIExplorer

def create_knowledge_graph(topic_data):
    """Create a NetworkX graph from topic data"""
    G = nx.Graph()
    
    # Add main topic node
    main_topic = topic_data["topic"]
    G.add_node(main_topic, size=25, color="#6200EA", title=topic_data["summary"], 
               type="main", level=0, node_id=str(uuid.uuid4()))
    
    # Add related concepts
    for concept in topic_data.get("related_concepts", []):
        concept_name = concept["name"]
        node_id = str(uuid.uuid4())
        G.add_node(concept_name, size=15, color="#7C4DFF", title=concept["summary"], 
                   type="concept", level=1, parent=main_topic, node_id=node_id)
        G.add_edge(main_topic, concept_name, title=concept["relation"], weight=1)
    
    # Add subtopics if they exist
    for subtopic in topic_data.get("subtopics", []):
        subtopic_name = subtopic["name"]
        node_id = str(uuid.uuid4())
        G.add_node(subtopic_name, size=20, color="#3949AB", title=subtopic["summary"], 
                   type="subtopic", level=1, parent=main_topic, node_id=node_id)
        G.add_edge(main_topic, subtopic_name, title="subtopic", weight=1)
    
    return G

def add_subnodes_to_graph(G, node_name, subnodes_data):
    """Add subnodes to the graph for a selected node"""
    # Get the node's level
    parent_level = G.nodes[node_name].get('level', 0)
    parent_id = G.nodes[node_name].get('node_id')
    
    # Add subnodes
    for subnode in subnodes_data.get('related_concepts', []):
        subnode_name = subnode["name"]
        node_id = str(uuid.uuid4())
        
        # Check if node already exists
        if subnode_name not in G:
            # Create a new node with a different color based on level
            colors = ["#E91E63", "#00BCD4", "#FF9800", "#4CAF50", "#9C27B0"]
            level_color = colors[min((parent_level + 1) % len(colors), len(colors) - 1)]
            
            G.add_node(
                subnode_name, 
                size=12, 
                color=level_color, 
                title=subnode["summary"], 
                type="sub-concept", 
                level=parent_level + 1,
                parent=node_name,
                node_id=node_id
            )
            
            G.add_edge(
                node_name, 
                subnode_name, 
                title=subnode.get("relation", "related to"), 
                weight=1
            )
    
    return G

def convert_to_pyvis(nx_graph, click_callback=True):
    """Convert NetworkX graph to PyVis for HTML visualization with click events"""
    pyvis_net = Network(height="600px", width="100%", bgcolor="#FFFFFF", font_color="black", select_menu=True, cdn_resources="remote")
    
    # Configure physics for better visualization
    pyvis_net.barnes_hut(
        gravity=-8000,        # More negative value for more repulsion
        central_gravity=0.8,  # Higher value to keep nodes more centered
        spring_length=200,    # More space between nodes
        spring_strength=0.05, # Weaker spring for more flexibility
        damping=0.9,          # Less oscillation
        overlap=0            # Prevent node overlap
    )
    
    # Add nodes and edges from NetworkX
    for node in nx_graph.nodes():
        node_attrs = nx_graph.nodes[node]
        pyvis_net.add_node(
            node, 
            label=node, 
            title=node_attrs.get("title", ""),
            size=node_attrs.get("size", 15),
            color=node_attrs.get("color", "#7C4DFF"),
            # Store additional attributes for access in JS events
            level=node_attrs.get("level", 0),
            node_type=node_attrs.get("type", "concept"),
            node_id=node_attrs.get("node_id", "")
        )
    
    for edge in nx_graph.edges():
        edge_attrs = nx_graph.edges[edge]
        weight = edge_attrs.get("weight", 1)
        pyvis_net.add_edge(
            edge[0], 
            edge[1],
            title=edge_attrs.get("title", ""),
            value=weight,  # Edge thickness
            arrowStrikethrough=False
        )
    
    # Create options dictionary
    options = {
        "nodes": {
            "font": {
                "size": 12,
                "face": "Roboto"
            },
            "borderWidth": 2,
            "shadow": True
        },
        "edges": {
            "color": {
                "inherit": True
            },
            "smooth": {
                "type": "continuous",
                "forceDirection": "none"
            },
            "shadow": True,
            "width": 1.5
        },
        "interaction": {
            "hover": True,
            "navigationButtons": True,
            "keyboard": True,
            "tooltipDelay": 300,
            "selectConnectedEdges": True,
            "hoverConnectedEdges": True
        },
        "physics": {
            "stabilization": {
                "iterations": 100
            }
        },
        "manipulation": {
            "enabled": False
        }
    }
    
    # Set options
    pyvis_net.options = options
    
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
    st.markdown("<h1 class='main-header'>🌳 Infinite Knowledge Tree</h1>", unsafe_allow_html=True)
    
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
    if 'selected_node_id' not in st.session_state:
        st.session_state.selected_node_id = None
    if 'show_node_details' not in st.session_state:
        st.session_state.show_node_details = False
    if 'load_tree_id' not in st.session_state:
        st.session_state.load_tree_id = None
    if 'load_topic' not in st.session_state:
        st.session_state.load_topic = None
    if 'subnodes_expanded' not in st.session_state:
        st.session_state.subnodes_expanded = set()
    if 'auto_expand' not in st.session_state:
        st.session_state.auto_expand = False
    if 'expansion_queue' not in st.session_state:
        st.session_state.expansion_queue = []
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### 🔍 Exploration Controls")
        
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
            max_value=2,  # Increased max depth for more expansion
            value=st.session_state.exploration_depth,
            help="Higher depth = more detailed information but slower response"
        )
        
        # Update session state if depth changed
        if exploration_depth != st.session_state.exploration_depth:
            st.session_state.exploration_depth = exploration_depth
        
        # Auto-expand toggle
        st.session_state.auto_expand = st.toggle(
            "Auto-expand nodes",
            value=st.session_state.auto_expand,
            help="Automatically expand nodes to create an infinite mindmap"
        )
        
        # History of explored topics
        if st.session_state.authenticated:
            st.divider()
            st.markdown("### 📚 Recent Topics")
            db = get_db_connection()
            if db.get_knowledge_tree(st.session_state.user_id):
                recent_trees = db.get_knowledge_tree(st.session_state.user_id)[:5]
                
                for tree in recent_trees:
                    if st.button(f"📌 {tree.get('topic', 'Untitled')}", key=f"history_{tree.get('_id', '')}"):
                        st.session_state.load_tree_id = str(tree.get('_id', ''))
                        st.session_state.load_topic = tree.get('topic', '')
                        st.rerun()
            else :
                pass
                    
    
    # Check if we should load a tree from history
    if st.session_state.load_tree_id and st.session_state.load_topic:
        db = get_db_connection()
        tree = db.get_knowledge_tree_by_id(st.session_state.load_tree_id)
        
        if tree:
            # Set topic
            st.session_state.topic = st.session_state.load_topic
            
            # Reconstruct knowledge graph from stored data
            G = nx.Graph()
            
            # Add nodes
            for node_id, node_data in tree.get('nodes', {}).items():
                G.add_node(
                    node_id,
                    **node_data  # Add all stored attributes
                )
            
            # Add edges
            for edge_key, edge_data in tree.get('edges', {}).items():
                # Edge key is in format "node1_node2"
                nodes = edge_key.split('_')
                if len(nodes) >= 2:  # Make sure we have valid edge data
                    G.add_edge(nodes[0], nodes[1], **edge_data)
            
            # Store the reconstructed graph
            st.session_state.graph = G
            
            # Set current node to main topic
            st.session_state.current_node = st.session_state.topic
            
            # Update nodes explored
            st.session_state.nodes_explored = set([st.session_state.topic])
            
            # Reset exploration time
            st.session_state.exploration_start_time = time.time()
            
            # Clear load flags
            st.session_state.load_tree_id = None
            st.session_state.load_topic = None
    
    # Main content area
    # Topic input and explore button
    topic_input = st.text_input(
        "Enter a topic to explore",
        value=st.session_state.topic,
        help="Type any topic you want to learn about"
    )
    
    if topic_input != st.session_state.topic:
        st.session_state.topic = topic_input
    
    # Explore button
    if st.button("🔍 Explore Topic", disabled=not st.session_state.topic, key="explore_topic_btn"):
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
            
            # Initialize expansion queue for auto-expand
            st.session_state.expansion_queue = [st.session_state.topic]
            
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
    
    # Auto-expand logic
    if st.session_state.auto_expand and st.session_state.graph and st.session_state.expansion_queue:
        # Get next node to expand
        node_to_expand = st.session_state.expansion_queue.pop(0)
        
        # Check if node exists and hasn't been expanded yet
        if (node_to_expand in st.session_state.graph.nodes() and 
            node_to_expand not in st.session_state.subnodes_expanded):
            
            with st.spinner(f"Auto-expanding {node_to_expand}..."):
                # Initialize AI explorer
                explorer = AIExplorer(
                    provider="google" if ai_provider == "Google Generative AI" else "groq"
                )
                
                # Get subnodes for this concept
                subnodes_data = explorer.get_related_concepts(node_to_expand)
                
                # Update graph with new subnodes
                st.session_state.graph = add_subnodes_to_graph(
                    st.session_state.graph, 
                    node_to_expand, 
                    subnodes_data
                )
                
                # Mark node as expanded
                st.session_state.subnodes_expanded.add(node_to_expand)
                
                # Update nodes explored count
                st.session_state.nodes_explored.add(node_to_expand)
                
                # Add new nodes to expansion queue
                for subnode in subnodes_data:
                    if subnode["name"] not in st.session_state.expansion_queue:
                        st.session_state.expansion_queue.append(subnode["name"])
                
                # Save updated graph to database
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
                    
                    # Get existing tree ID or create new
                    tree = db.get_knowledge_tree(st.session_state.user_id, st.session_state.topic)
                    tree_id = str(tree[0]["_id"]) if tree and len(tree) > 0 else None
                    
                    # Update tree in database
                    tree_id = db.save_knowledge_tree(
                        st.session_state.user_id,
                        st.session_state.topic,
                        nodes_dict,
                        edges_dict,
                        tree_id=tree_id,
                        update=True
                    )
            
            # Rerun to continue auto-expansion
            st.rerun()
    
    # Display visualization if graph exists
    if st.session_state.graph:
        # Interactive visualization with PyVis
        pyvis_net = convert_to_pyvis(st.session_state.graph)
        
        # Save HTML
        pyvis_net.save_graph("assets/static/temp_graph.html")
        
        # Read the saved HTML
        with open("assets/static/temp_graph.html", "r", encoding="utf-8") as f:
            html_data = f.read()
        
        # Add custom JavaScript for node click events with enhanced functionality
        custom_js = """
        <script>
        // Wait for network to be fully loaded
        setTimeout(function() {
            try {
                // Get the network instance
                const network = document.getElementsByClassName('vis-network')[0].network;
                
                // Add click event listener
                network.on("click", function(params) {
                    if (params.nodes.length > 0) {
                        var nodeId = params.nodes[0];
                        var node = network.body.data.nodes.get(nodeId);
                        
                        // Visual feedback for node selection
                        network.body.data.nodes.update({
                            id: nodeId,
                            borderWidth: 3,
                            borderColor: "#FF5722"
                        });
                        
                        // Send node info to Streamlit via sessionStorage
                        sessionStorage.setItem('selectedNode', JSON.stringify({
                            id: nodeId,
                            label: node.label,
                            node_id: node.node_id,
                            type: node.node_type,
                            level: node.level
                        }));
                        
                        // Trigger a click on a hidden button to refresh Streamlit
                        document.getElementById('node_selected_trigger').click();
                    }
                });
                
                // Add double-click event for quick expansion
                network.on("doubleClick", function(params) {
                    if (params.nodes.length > 0) {
                        var nodeId = params.nodes[0];
                        var node = network.body.data.nodes.get(nodeId);
                        
                        // Send node info with expansion flag
                        sessionStorage.setItem('expandNode', JSON.stringify({
                            id: nodeId,
                            label: node.label,
                            node_id: node.node_id
                        }));
                        
                        // Trigger expand action
                        document.getElementById('expand_node_trigger').click();
                    }
                });
            } catch (e) {
                console.error("Error setting up node click handler:", e);
            }
        }, 1000);
        </script>
        """
        
        # Create hidden buttons for node selection and expansion
        hidden_buttons = """
        <button id="node_selected_trigger" style="display:none;">Node Selected</button>
        <button id="expand_node_trigger" style="display:none;">Expand Node</button>
        <script>
        // Node selection handler
        const button = document.getElementById('node_selected_trigger');
        button.addEventListener('click', function() {
            const selectedNode = sessionStorage.getItem('selectedNode');
            if (selectedNode) {
                const encodedNode = encodeURIComponent(selectedNode);
                const url = new URL(window.location.href);
                url.searchParams.set('selected_node', encodedNode);
                window.location.href = url.toString();
            }
        });

        // Node expansion handler
        const expandButton = document.getElementById('expand_node_trigger');
        expandButton.addEventListener('click', function() {
            const expandNode = sessionStorage.getItem('expandNode');
            if (expandNode) {
                const encodedNode = encodeURIComponent(expandNode);
                const url = new URL(window.location.href);
                url.searchParams.set('expand_node', encodedNode);
                window.location.href = url.toString();
            }
        });
        </script>
        """
        
        # Insert custom JS and hidden buttons before the closing body tag
        html_data = html_data.replace('</body>', custom_js + hidden_buttons + '</body>')
        
        # Display graph with custom height
        components.html(html_data, height=600)
        
        # Process node selection from URL parameters
        query_params = st.query_params
        if "selected_node" in query_params:
            try:
                node_data = json.loads(query_params["selected_node"][0])
                st.session_state.selected_node_id = node_data["id"]
                st.session_state.current_node = node_data["id"]
                st.session_state.show_node_details = True
                
                # Update URL to remove query parameter
                st.experimental_set_query_params()
            except Exception as e:
                st.error(f"Error processing selected node: {e}")
                
        # Handle expansion request from double-click
        if "expand_node" in query_params:
            try:
                node_data = json.loads(query_params["expand_node"][0])
                node_to_expand = node_data["id"]
                
                # Only expand if node exists and hasn't been expanded yet
                if (node_to_expand in st.session_state.graph.nodes() and 
                    node_to_expand not in st.session_state.subnodes_expanded):
                    
                    with st.spinner(f"Expanding {node_to_expand}..."):
                        # Initialize AI explorer
                        explorer = AIExplorer(
                            provider="google" if ai_provider == "Google Generative AI" else "groq"
                        )
                        
                        # Get subnodes for this concept
                        subnodes_data = explorer.explore_subtopic(
                            main_topic=st.session_state.topic,
                            subtopic=node_to_expand
                        )
                        
                        # Update graph with new subnodes
                        st.session_state.graph = add_subnodes_to_graph(
                            st.session_state.graph, 
                            node_to_expand, 
                            subnodes_data
                        )
                        
                        # Mark node as expanded
                        st.session_state.subnodes_expanded.add(node_to_expand)
                        
                        # Update nodes explored count
                        st.session_state.nodes_explored.add(node_to_expand)
                        
                        # Set current node to the expanded node
                        st.session_state.current_node = node_to_expand
                        st.session_state.selected_node_id = node_to_expand
                        st.session_state.show_node_details = True
                        
                        # Save updated graph to database if authenticated
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
                            
                            # Update tree in database
                            tree = db.get_knowledge_tree(st.session_state.user_id, st.session_state.topic)
                            tree_id = str(tree[0]["_id"]) if tree and len(tree) > 0 else None
                            
                            db.save_knowledge_tree(
                                st.session_state.user_id,
                                st.session_state.topic,
                                nodes_dict,
                                edges_dict,
                                tree_id=tree_id,
                                update=True
                            )
                
                # Update URL to remove query parameter
                st.experimental_set_query_params()
            except Exception as e:
                st.error(f"Error processing node expansion: {e}")
    
    # Node details section with enhanced UI
    if st.session_state.graph and st.session_state.current_node:
        current_node = st.session_state.current_node
        
        if current_node in st.session_state.graph.nodes():
            node_attrs = st.session_state.graph.nodes[current_node]
            
            # Display node information with enhanced UI
            with st.expander(f"📖 {current_node}", expanded=True):
                st.markdown(node_attrs.get('title', 'No description available'))
                
                # Node metadata with better layout
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Type:** {node_attrs.get('type', 'concept').title()}")
                with col2:
                    level = node_attrs.get('level', 0)
                    st.markdown(f"**Depth Level:** {level}")
                with col3:
                    if node_attrs.get('parent'):
                        parent = node_attrs.get('parent')
                        st.markdown(f"**Parent:** {parent}")
                
                # More visible expansion controls
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if current_node not in st.session_state.subnodes_expanded:
                        expand_btn = st.button("🌱 Expand this concept", 
                                    key=f"expand_{current_node}",
                                    type="primary",
                                    use_container_width=True)
                    else:
                        expand_btn = st.button("✓ Already expanded", 
                                    key=f"expand_{current_node}",
                                    disabled=True,
                                    use_container_width=True)
                        
                    if expand_btn and current_node not in st.session_state.subnodes_expanded:
                        with st.spinner(f"Expanding {current_node}..."):
                            # Initialize AI explorer
                            explorer = AIExplorer(
                                provider="google" if ai_provider == "Google Generative AI" else "groq"
                            )
                            
                            # Get subnodes for this concept
                            subnodes_data = explorer.explore_subtopic(
                                main_topic=st.session_state.topic,
                                subtopic=current_node
                            )
                            
                            # Update graph with new subnodes
                            st.session_state.graph = add_subnodes_to_graph(
                                st.session_state.graph, 
                                current_node, 
                                subnodes_data
                            )
                            
                            # Mark node as expanded
                            st.session_state.subnodes_expanded.add(current_node)
                            
                            # Update nodes explored count
                            st.session_state.nodes_explored.add(current_node)
                            
                            # Save updated graph to database
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
                                
                                # Get existing tree ID or create new
                                tree = db.get_knowledge_tree(st.session_state.user_id, st.session_state.topic)
                                tree_id = str(tree[0]["_id"]) if tree and len(tree) > 0 else None
                                
                                # Update tree in database
                                db.save_knowledge_tree(
                                    st.session_state.user_id,
                                    st.session_state.topic,
                                    nodes_dict,
                                    edges_dict,
                                    tree_id=tree_id,
                                    update=True
                            )
                        
                        st.rerun()
                
                # Detailed explanation
                if st.button("📚 Get detailed explanation", key=f"explain_{current_node}"):
                    with st.spinner(f"Generating detailed explanation..."):
                        explorer = AIExplorer(
                            provider="google" if ai_provider == "Google Generative AI" else "groq"
                        )
                        explanation = explorer.get_detailed_explanation(current_node)
                        st.markdown("### Detailed Explanation")
                        st.markdown(explanation)
    
    # If user is authenticated, log session when they leave
    if st.session_state.authenticated and st.session_state.graph:
        current_time = time.time()
        time_spent = current_time - st.session_state.exploration_start_time
        
        # Log session after 30 seconds of exploration
        if time_spent > 30 and len(st.session_state.nodes_explored) > 0:
            db = get_db_connection()
            
            # Get tree ID safely
            tree = db.get_knowledge_tree(st.session_state.user_id, st.session_state.topic)
            tree_id = str(tree[0]["_id"]) if tree and len(tree) > 0 else None
            
            if not tree_id:
                nodes_dict = {}
                edges_dict = {}
                
                for node in st.session_state.graph.nodes():
                    nodes_dict[node] = dict(st.session_state.graph.nodes[node])
                
                for edge in st.session_state.graph.edges():
                    edge_key = f"{edge[0]}_{edge[1]}"
                    edges_dict[edge_key] = dict(st.session_state.graph.edges[edge])
                
                tree_id = db.save_knowledge_tree(
                    st.session_state.user_id,
                    st.session_state.topic,
                    nodes_dict,
                    edges_dict
                )
            
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