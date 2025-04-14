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
    
    # Get comprehensive learning stats
    learning_stats = db.get_learning_stats(st.session_state.user_id)
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Advanced Analytics", "📑 Sessions", "🔍 Search"])
    
    with tab1:
        st.markdown("### 📊 Learning Analytics")
        
        # Display summary stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sessions", learning_stats["total_sessions"])
        
        with col2:
            st.metric("Topics Explored", learning_stats["topics_explored"])
            
        with col3:
            total_hours = learning_stats["total_time"] / 3600
            st.metric("Total Hours", f"{total_hours:.1f}")
            
        with col4:
            st.metric("Learning Streak", f"{learning_stats['learning_streak']} days")
        
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
                title="Nodes Explored per Day",
                labels={"nodes_explored": "Nodes", "date": "Date"},
                markers=True
            )
            
            fig.update_traces(line_color="#00BFA5")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.markdown("### 📈 Advanced Analytics")
        
        # Topic knowledge depth analysis
        topic_depth_data = []
        
        for topic, data in topics.items():
            avg_nodes_per_session = data["nodes_explored"] / data["sessions"] if data["sessions"] > 0 else 0
            avg_time_per_node = data["total_time"] / data["nodes_explored"] if data["nodes_explored"] > 0 else 0
            
            topic_depth_data.append({
                "topic": topic,
                "avg_nodes_per_session": avg_nodes_per_session,
                "avg_time_per_node": avg_time_per_node / 60,  # Convert to minutes
                "total_sessions": data["sessions"]
            })
        
        topic_depth_df = pd.DataFrame(topic_depth_data)
        
        if not topic_depth_df.empty:
            # Topic depth scatter plot
            fig = px.scatter(
                topic_depth_df,
                x="avg_nodes_per_session",
                y="avg_time_per_node",
                size="total_sessions",
                color="total_sessions",
                hover_name="topic",
                size_max=40,
                title="Topic Exploration Depth Analysis",
                labels={
                    "avg_nodes_per_session": "Avg. Nodes per Session",
                    "avg_time_per_node": "Avg. Minutes per Node",
                    "total_sessions": "Total Sessions"
                }
            )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            # Learning efficiency over time
            if len(history) > 3:  # Only show if we have enough data
                efficiency_data = []
                
                # Sort history by timestamp
                sorted_history = sorted(history, key=lambda x: x["timestamp"])
                
                for i, session in enumerate(sorted_history):
                    if session["time_spent"] > 0 and len(session["nodes_explored"]) > 0:
                        efficiency = len(session["nodes_explored"]) / (session["time_spent"] / 60)  # Nodes per minute
                        efficiency_data.append({
                            "session_number": i + 1,
                            "date": session["timestamp"].date(),
                            "efficiency": efficiency,
                            "topic": session["topic"]
                        })
                
                if efficiency_data:
                    eff_df = pd.DataFrame(efficiency_data)
                    
                    fig = px.line(
                        eff_df,
                        x="session_number",
                        y="efficiency",
                        title="Learning Efficiency Over Time (Nodes per Minute)",
                        labels={
                            "session_number": "Session Number",
                            "efficiency": "Efficiency (Nodes/Minute)",
                            "topic": "Topic"
                        },
                        hover_data=["date", "topic"],
                        markers=True
                    )
                    
                    fig.update_traces(line_color="#FF4081")
                    st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### 📑 Session History")
        
        # Create a dataframe of sessions
        sessions_data = []
        
        for session in history:
            sessions_data.append({
                "date": session["timestamp"].strftime("%Y-%m-%d %H:%M"),
                "topic": session["topic"],
                "time_spent": format_time_spent(session["time_spent"]),
                "nodes_explored": len(session["nodes_explored"]),
                "raw_timestamp": session["timestamp"],  # For sorting
                "session_id": str(session["_id"]),  # For identification
                "tree_id": session["tree_id"]  # For linking to the graph
            })
        
        # Sort by timestamp (most recent first)
        sessions_df = pd.DataFrame(sessions_data).sort_values("raw_timestamp", ascending=False)
        
        if not sessions_df.empty:
            # Remove raw timestamp from display
            display_df = sessions_df.drop(columns=["raw_timestamp", "session_id", "tree_id"])
            
            # Display table with highlighting
            st.dataframe(
                display_df,
                hide_index=True,
                column_config={
                    "date": "Date & Time",
                    "topic": "Topic",
                    "time_spent": "Time Spent",
                    "nodes_explored": "Nodes Explored"
                },
                use_container_width=True
            )
            
            # Session selection for details
            selected_session = st.selectbox(
                "Select a session to view details:",
                options=sessions_df["session_id"].tolist(),
                format_func=lambda x: f"{sessions_df[sessions_df['session_id'] == x]['date'].values[0]} - {sessions_df[sessions_df['session_id'] == x]['topic'].values[0]}"
            )
            
            if selected_session:
                # Get session details
                session_row = sessions_df[sessions_df["session_id"] == selected_session].iloc[0]
                
                st.markdown(f"### Session Details: {session_row['topic']}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Date", session_row["date"])
                
                with col2:
                    st.metric("Time Spent", session_row["time_spent"])
                
                with col3:
                    st.metric("Nodes Explored", session_row["nodes_explored"])
                
                # Option to revisit this topic in visualizer
                if st.button(f"📚 Continue exploring '{session_row['topic']}'"):
                    # Store tree_id in session state to load the graph in visualizer
                    st.session_state.load_tree_id = session_row["tree_id"]
                    st.session_state.load_topic = session_row["topic"]
                    st.session_state.current_page = "visualizer"
                    st.rerun()
    
    with tab4:
        st.markdown("### 🔍 Search Your Learning History")
        
        # Search input
        search_query = st.text_input("Search topics or concepts you've explored:")
        
        if search_query:
            # Search in database
            search_results = db.search_learning_history(st.session_state.user_id, search_query)
            
            if search_results:
                st.success(f"Found {len(search_results)} results for '{search_query}'")
                
                # Display search results
                for result in search_results:
                    with st.expander(f"**{result['topic']}** - {result['timestamp'].strftime('%Y-%m-%d')}"):
                        st.write(f"**Time spent:** {format_time_spent(result['time_spent'])}")
                        st.write(f"**Nodes explored:** {len(result['nodes_explored'])}")
                        
                        if "nodes_explored" in result and result["nodes_explored"]:
                            st.write("**Concepts explored:**")
                            st.write(", ".join(result["nodes_explored"]))
                        
                        # Button to revisit this topic
                        if st.button(f"Continue exploring '{result['topic']}'", key=f"search_{result['_id']}"):
                            st.session_state.load_tree_id = result["tree_id"]
                            st.session_state.load_topic = result["topic"]
                            st.session_state.current_page = "visualizer"
                            st.rerun()
            else:
                st.info(f"No results found for '{search_query}'")