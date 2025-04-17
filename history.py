import streamlit as st
import pandas as pd
import base64
import io
from datetime import datetime
from db import get_all_sessions, get_session_by_id, search_sessions
import tempfile
import os
from visualizer import format_time

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

def get_pdf_download_link(pdf_binary, filename="nodelearn_summary.pdf"):
    """Generate a download link for a PDF file stored in binary format."""
    b64 = base64.b64encode(pdf_binary).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="download-btn">Download PDF</a>'
    return href

def show_history():
    st.title("📚 NodeLearn - Session History")
    
    # Custom CSS for styling
    st.markdown("""
    <style>
        .download-btn {
            display: inline-block;
            padding: 8px 12px;
            background-color: #6200EE;
            color: white;
            border-radius: 4px;
            text-decoration: none;
            margin-top: 10px;
        }
        .download-btn:hover {
            background-color: #3700B3;
        }
        .css-1v3fvcr {
            background-color: #121212;
            color: #FFFFFF;
        }
        .css-18e3th9 {
            padding-top: 2rem;
        }
        .session-card {
            background-color: #1E1E1E;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .session-title {
            color: #BB86FC;
            font-weight: bold;
            font-size: 1.2em;
        }
        .session-stats {
            margin-top: 10px;
            color: #B3B3B3;
        }
        .session-date {
            font-size: 0.9em;
            color: #03DAC6;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Search and filter sidebar
    with st.sidebar:
        st.subheader("🔍 Search & Filter")
        
        search_query = st.text_input("Search by topic or content")
        
        date_options = ["All Time", "Today", "Last Week", "Last Month"]
        date_filter = st.selectbox("Time Period", date_options)
        
        st.divider()
        
        sort_options = ["Newest First", "Oldest First", "Most Topics", "Longest Duration"]
        sort_by = st.selectbox("Sort By", sort_options)
        
        if st.button("Apply Filters", key="filter_button"):
            st.session_state.filtered = True
        
        if st.button("Reset Filters", key="reset_button"):
            st.session_state.filtered = False
    
    # Initialize session state
    if 'filtered' not in st.session_state:
        st.session_state.filtered = False
    if 'selected_session' not in st.session_state:
        st.session_state.selected_session = None
    
    # Main content area
    if st.session_state.selected_session:
        # Display selected session details
        session = get_session_by_id(st.session_state.selected_session)
        
        # Back button
        if st.button("← Back to All Sessions"):
            st.session_state.selected_session = None
            st.rerun()
        
        st.header(f"Session from {session.get('created_at', 'Unknown date')}")
        
        # Session stats
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        with stats_col1:
            st.metric("Topics Explored", len(session.get('nodes', [])))
        with stats_col2:
            st.metric("Connections Made", len(session.get('edges', [])))
        with stats_col3:
            st.metric("Total Time", format_time(session.get('total_time', 0)))
        
        # Topics explored
        st.subheader("Topics Explored")
        
        # Create a DataFrame for better display
        topics_data = []
        for node in session.get('nodes', []):
            topics_data.append({
                "Topic": node,
                "Time Spent": format_time(session.get('topic_times', {}).get(node, 0)),
                "AI Level": session.get('detail_level', 'Intermediate')
            })
        
        if topics_data:
            topics_df = pd.DataFrame(topics_data)
            st.dataframe(topics_df, use_container_width=True)
        else:
            st.info("No topics data available for this session.")
        
        # Knowledge map (static representation)
        st.subheader("Knowledge Map")
        
        # Simple visualization of the knowledge tree structure
        import networkx as nx
        import matplotlib.pyplot as plt
        
        G = nx.DiGraph()
        for node in session.get('nodes', []):
            G.add_node(node)
        
        for edge in session.get('edges', []):
            G.add_edge(edge[0], edge[1])
        
        fig, ax = plt.subplots(figsize=(10, 8))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color="#BB86FC", 
                edge_color="#03DAC6", node_size=1500, font_size=10,
                font_color="white", font_weight="bold", ax=ax)
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # Display download link for PDF if available
        if 'pdf' in session:
            st.subheader("Session Summary")
            st.markdown(get_pdf_download_link(session['pdf']), unsafe_allow_html=True)
        
    else:
        # Get session data based on filters
        if st.session_state.filtered and search_query:
            sessions = search_sessions(search_query)
        else:
            sessions = get_all_sessions()
        
        # Apply date filter
        filtered_sessions = []
        now = datetime.now()
        
        for session in sessions:
            created_at = session.get('created_at')
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except:
                    created_at = datetime.now()  # Default if parsing fails
            
            if date_filter == "All Time":
                filtered_sessions.append(session)
            elif date_filter == "Today":
                if (now - created_at).days < 1:
                    filtered_sessions.append(session)
            elif date_filter == "Last Week":
                if (now - created_at).days < 7:
                    filtered_sessions.append(session)
            elif date_filter == "Last Month":
                if (now - created_at).days < 30:
                    filtered_sessions.append(session)
        
        # Apply sorting
        if sort_by == "Newest First":
            filtered_sessions = sorted(filtered_sessions, 
                                     key=lambda x: x.get('created_at', ''), 
                                     reverse=True)
        elif sort_by == "Oldest First":
            filtered_sessions = sorted(filtered_sessions, 
                                     key=lambda x: x.get('created_at', ''))
        elif sort_by == "Most Topics":
            filtered_sessions = sorted(filtered_sessions, 
                                     key=lambda x: len(x.get('nodes', [])), 
                                     reverse=True)
        elif sort_by == "Longest Duration":
            filtered_sessions = sorted(filtered_sessions, 
                                     key=lambda x: x.get('total_time', 0), 
                                     reverse=True)
        
        # Display session cards
        if filtered_sessions:
            for i, session in enumerate(filtered_sessions):
                with st.container():
                    st.markdown(f"""
                    <div class="session-card">
                        <div class="session-title">{session.get('nodes', [])[0] if session.get('nodes') else 'Untitled Session'}</div>
                        <div class="session-date">{session.get('created_at', 'Unknown date')}</div>
                        <div class="session-stats">
                            Topics: {len(session.get('nodes', []))} | 
                            Connections: {len(session.get('edges', []))} | 
                            Time: {format_time(session.get('total_time', 0))}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Add buttons for each session
                    col1, col2, col3 = st.columns([1, 1, 2])
                    with col1:
                        if st.button("View Details", key=f"view_{i}"):
                            st.session_state.selected_session = session.get('_id')
                            st.rerun()
                    
                    with col2:
                        if 'pdf' in session:
                            st.markdown(get_pdf_download_link(session['pdf'], 
                                f"{session.get('nodes', [])[0] if session.get('nodes') else 'session'}_summary.pdf"), 
                                unsafe_allow_html=True)
        else:
            st.info("No sessions found with the current filters. Try adjusting your search criteria.")
            
            # Call to action for new session
            st.markdown("""
            <div style="text-align: center; margin-top: 50px;">
                <h3 style="color: #BB86FC;">Ready to start a new knowledge exploration?</h3>
                <p style="color: #B3B3B3;">Begin your learning journey by creating a new session.</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Create New Session", type="primary"):
                from streamlit_extras.switch_page_button import switch_page
                switch_page("visualizer")
