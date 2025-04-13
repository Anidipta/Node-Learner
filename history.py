import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
from db import get_db_connection

def format_time_spent(seconds):
    """Format seconds into readable time"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"

def show_history():
    """Display user's learning history and analytics"""
    st.markdown("<h1 class='main-header'>📚 Learning History</h1>", unsafe_allow_html=True)
    
    # Check if user is authenticated
    if not st.session_state.authenticated:
        st.warning("Please log in to view your learning history")
        if st.button("Go to Login"):
            st.session_state.current_page = 'login'
            st.rerun()
        return
    
    # Connect to database
    db = get_db_connection()
    
    # Get user's learning history
    history = db.get_learning_history(st.session_state.user_id, limit=100)
    
    if not history:
        st.info("You haven't explored any topics yet. Start learning to build your history!")
        if st.button("Explore Topics"):
            st.session_state.current_page = 'visualizer'
            st.rerun()
        return
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📑 Sessions", "🔍 Search"])
    
    with tab1:
        st.markdown("### 📊 Learning Analytics")
        
        # Process data for analytics
        topics = {}
        time_data = []
        nodes_data = []
        
        for session in history:
            topic = session["topic"]
            timestamp = session["timestamp"]
            time_spent = session["time_spent"]
            nodes_explored = len(session["nodes_explored"])
            
            # Aggregate by topic
            if topic not in topics:
                topics[topic] = {
                    "sessions": 0,
                    "total_time": 0,
                    "nodes_explored": 0
                }
            
            topics[topic]["sessions"] += 1
            topics[topic]["total_time"] += time_spent
            topics[topic]["nodes_explored"] += nodes_explored
            
            # Data for time series
            time_data.append({
                "date": timestamp.date(),
                "time_spent": time_spent / 60  # Convert to minutes
            })
            
            nodes_data.append({
                "date": timestamp.date(),
                "nodes_explored": nodes_explored
            })
        
        # Create analytics charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Most explored topics chart
            topic_df = pd.DataFrame([
                {"topic": topic, "sessions": data["sessions"]}
                for topic, data in topics.items()
            ])
            
            if not topic_df.empty:
                topic_df = topic_df.sort_values("sessions", ascending=False).head(10)
                
                fig = px.bar(
                    topic_df, 
                    x="sessions", 
                    y="topic", 
                    orientation='h',
                    title="Most Explored Topics",
                    labels={"sessions": "Number of Sessions", "topic": "Topic"},
                    color="sessions",
                    color_continuous_scale=px.colors.sequential.Purples
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Time spent per topic chart
            time_df = pd.DataFrame([
                {"topic": topic, "time_spent": data["total_time"] / 60}  # Convert to minutes
                for topic, data in topics.items()
            ])
            
            if not time_df.empty:
                time_df = time_df.sort_values("time_spent", ascending=False).head(10)
                
                fig = px.bar(
                    time_df, 
                    x="time_spent", 
                    y="topic", 
                    orientation='h',
                    title="Time Spent per Topic (minutes)",
                    labels={"time_spent": "Time (minutes)", "topic": "Topic"},
                    color="time_spent",
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Time series chart
        st.markdown("### 📈 Learning Activity Over Time")
        
        # Process data for time series
        df_time = pd.DataFrame(time_data)
        if not df_time.empty:
            df_time = df_time.groupby("date").sum().reset_index()
            df_time = df_time.sort_values("date")
            
            fig = px.line(
                df_time, 
                x="date", 
                y="time_spent",
                title="Time Spent Learning per Day (minutes)",
                labels={"time_spent": "Time (minutes)", "date": "Date"},
                markers=True
            )
            
            fig.update_traces(line_color="#6200EA")
            st.plotly_chart(fig, use_container_width=True)
        
        # Nodes explored
        df_nodes = pd.DataFrame(nodes_data)
        if not df_nodes.empty:
            df_nodes = df_nodes.groupby("date").sum().reset_index()
            df_nodes = df_nodes.sort_values("date")
            
            fig = px.line(
                df_nodes, 
                x="date", 
                y="nodes_explored",
                title="Concepts Explored per Day",
                labels={"nodes_explored": "Nodes Explored", "date": "Date"},
                markers=True
            )
            
            fig.update_traces(line_color="#3949AB")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("### 📑 Learning Sessions")
        
        # Sort by most recent first
        sessions = sorted(history, key=lambda x: x["timestamp"], reverse=True)
        
        # Display sessions
        for i, session in enumerate(sessions):
            with st.expander(f"{session['topic']} - {session['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"**Topic:** {session['topic']}")
                
                with col2:
                    st.markdown(f"**Time Spent:** {format_time_spent(session['time_spent'])}")
                
                with col3:
                    st.markdown(f"**Nodes Explored:** {len(session['nodes_explored'])}")
                
                st.markdown("**Concepts Explored:**")
                st.write(", ".join(session["nodes_explored"]))
                
                # Button to revisit this topic
                if st.button(f"Revisit Topic", key=f"revisit_{i}"):
                    st.session_state.topic = session["topic"]
                    st.session_state.current_page = 'visualizer'
                    st.rerun()
    
    with tab3:
        st.markdown("### 🔍 Search Learning History")
        
        # Search box
        search_query = st.text_input("Search topics or concepts")
        
        if search_query:
            # Search in topics
            topic_results = db.search_topics(st.session_state.user_id, search_query)
            
            # Search in session nodes explored
            session_results = []
            for session in history:
                for node in session["nodes_explored"]:
                    if search_query.lower() in node.lower():
                        session_results.append(session)
                        break
            
            # Display results
            if topic_results or session_results:
                st.markdown(f"Found {len(topic_results)} topics and {len(session_results)} sessions matching '{search_query}'")
                
                # Display topic results
                if topic_results:
                    st.markdown("#### Topic Matches")
                    for topic in topic_results:
                        with st.expander(topic["topic"]):
                            st.markdown(f"**Created:** {topic.get('created_at', 'Unknown').strftime('%Y-%m-%d')}")
                            st.markdown(f"**Last Updated:** {topic.get('updated_at', 'Unknown').strftime('%Y-%m-%d')}")
                            
                            # Button to explore this topic
                            if st.button(f"Explore Topic", key=f"explore_{topic['topic']}"):
                                st.session_state.topic = topic["topic"]
                                st.session_state.current_page = 'visualizer'
                                st.rerun()
                
                # Display session results
                if session_results:
                    st.markdown("#### Session Matches")
                    for i, session in enumerate(session_results):
                        with st.expander(f"{session['topic']} - {session['timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                            st.markdown(f"**Time Spent:** {format_time_spent(session['time_spent'])}")
                            st.markdown(f"**Concepts Explored:** {', '.join(session['nodes_explored'])}")
                            
                            # Highlight matching nodes
                            st.markdown("**Matching Concepts:**")
                            matching_nodes = [node for node in session["nodes_explored"] if search_query.lower() in node.lower()]
                            st.write(", ".join(matching_nodes))
                            
                            # Button to revisit this topic
                            if st.button(f"Revisit Topic", key=f"revisit_search_{i}"):
                                st.session_state.topic = session["topic"]
                                st.session_state.current_page = 'visualizer'
                                st.rerun()
            else:
                st.info(f"No results found for '{search_query}'")
    
    # Export data button
    st.markdown("---")
    if st.button("📥 Export Learning History"):
        # Create DataFrame for export
        export_data = []
        for session in history:
            export_data.append({
                "Topic": session["topic"],
                "Date": session["timestamp"].strftime("%Y-%m-%d %H:%M"),
                "Time Spent (minutes)": round(session["time_spent"] / 60, 2),
                "Nodes Explored": len(session["nodes_explored"]),
                "Concepts": ", ".join(session["nodes_explored"])
            })
        
        df_export = pd.DataFrame(export_data)
        
        # Convert to CSV
        csv = df_export.to_csv(index=False)
        
        # Create download button
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"nodelearn_history_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
