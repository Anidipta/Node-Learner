import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from db import get_db_connection
import numpy as np
from bson.objectid import ObjectId

def show_dashboard():
    """
    Display a comprehensive dashboard with user details, statistics, and visualizations
    using data from MongoDB.
    """
    st.title("🚀 Learning Dashboard")
    
    # Get database connection
    db = get_db_connection()
    
    # Get user data from session state
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.warning("User data not available. Please log in again.")
        return
    
    # Create columns for layout
    col1, col2 = st.columns([1, 3])
    
    with col1:
        show_user_profile(db, user_id)
    
    with col2:
        show_stats_summary(db, user_id)
    
    # Learning activity timeline
    st.markdown("### 📊 Learning Activity")
    tab1, tab2, tab3 = st.tabs(["Weekly Progress", "Topic Distribution", "Knowledge Graph"])
    
    with tab1:
        show_activity_chart(db, user_id)
    
    with tab2:
        show_topic_distribution(db, user_id)
    
    with tab3:
        show_mini_knowledge_graph(db, user_id)
    
    # Recent activity and recommendations
    col_recent, col_rec = st.columns(2)
    
    with col_recent:
        show_recent_activity(db, user_id)
    
    with col_rec:
        show_recommendations(db, user_id)

def show_user_profile(db, user_id):
    """Display user profile information from database"""
    # Get user data from database
    user_data = db.users.find_one({"_id": ObjectId(user_id)})
    
    if not user_data:
        st.error("User data not found.")
        return
    
    # Profile container
    with st.container():
        st.markdown("### 👤 User Profile")
        
        # User avatar and info
        col_img, col_info = st.columns([1, 2])
        
        with col_img:
            # Display user avatar (placeholder or from user data)
            avatar_url = user_data.get('avatar_url', 'https://via.placeholder.com/150')
            st.image(avatar_url, width=100)
        
        with col_info:
            st.markdown(f"**Name:** {user_data.get('name', 'User')}")
            st.markdown(f"**Email:** {user_data.get('email', 'N/A')}")
            
            # Format join date if available
            joined_date = user_data.get('created_at', datetime.utcnow())
            if isinstance(joined_date, datetime):
                joined_formatted = joined_date.strftime("%B %d, %Y")
            else:
                joined_formatted = "N/A"
            
            st.markdown(f"**Joined:** {joined_formatted}")
            
            # Determine user level based on learning sessions
            learning_sessions = db.learning_sessions.find({"user_id": user_id}).count()
            if learning_sessions > 50:
                level = "Advanced"
            elif learning_sessions > 20:
                level = "Intermediate"
            else:
                level = "Beginner"
                
            st.markdown(f"**Level:** {level}")
        
        # Calculate streak
        streak = calculate_streak(db, user_id)
        st.markdown(f"🔥 **{streak} Day Streak**")
        streak_progress = st.progress(min(streak / 10, 1.0))
        
        # Favorite topics based on most used knowledge trees
        favorite_topics = get_favorite_topics(db, user_id)
        
        st.markdown("#### Favorite Topics")
        for topic in favorite_topics:
            st.markdown(f"- {topic}")
        
        # Quick actions
        st.markdown("#### Quick Actions")
        st.button("Edit Profile", key="edit_profile")
        st.button("Connect Google Calendar", key="connect_calendar")

def calculate_streak(db, user_id):
    """Calculate user's learning streak in days"""
    # Get recent sessions ordered by date
    sessions = list(db.learning_sessions.find(
        {"user_id": user_id}
    ).sort("timestamp", -1))
    
    if not sessions:
        return 0
    
    # Get unique dates
    dates = set()
    today = datetime.utcnow().date()
    
    for session in sessions:
        session_date = session.get('timestamp', datetime.utcnow()).date()
        if (today - session_date).days > 30:  # Only look at last 30 days
            break
        dates.add(session_date)
    
    # Calculate streak (consecutive days)
    streak = 0
    check_date = today
    
    while check_date in dates:
        streak += 1
        check_date = check_date - timedelta(days=1)
    
    return streak

def get_favorite_topics(db, user_id):
    """Get user's favorite topics based on usage"""
    # Get all knowledge trees for user
    trees = db.knowledge_trees.find({"user_id": user_id})
    
    # Count topics
    topic_counts = {}
    for tree in trees:
        topic = tree.get('topic', 'Unknown')
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    # Sort by count and return top 3
    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
    return [topic for topic, _ in sorted_topics[:3]] if sorted_topics else ["No topics yet"]

def show_stats_summary(db, user_id):
    """Display key statistics cards based on database data"""
    # Calculate stats
    stats = {
        'nodes_created': calculate_nodes_created(db, user_id),
        'connections': calculate_connections(db, user_id),
        'learning_hours': calculate_learning_hours(db, user_id),
        'completion_rate': calculate_completion_rate(db, user_id),
        'knowledge_score': calculate_knowledge_score(db, user_id)
    }
    
    # Weekly changes
    weekly_stats = {
        'nodes_created': calculate_nodes_created(db, user_id, days=7),
        'connections': calculate_connections(db, user_id, days=7),
        'learning_hours': calculate_learning_hours(db, user_id, days=7),
        'completion_rate': calculate_weekly_completion_delta(db, user_id),
        'knowledge_score': calculate_weekly_score_delta(db, user_id)
    }
    
    # Create metric cards for key stats
    st.markdown("### 📈 Learning Stats")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Knowledge Nodes", 
            value=stats['nodes_created'],
            delta=f"+{weekly_stats['nodes_created']} this week"
        )
    
    with col2:
        st.metric(
            label="Connections Made", 
            value=stats['connections'],
            delta=f"+{weekly_stats['connections']} this week"
        )
    
    with col3:
        st.metric(
            label="Learning Hours", 
            value=f"{stats['learning_hours']:.1f}h",
            delta=f"+{weekly_stats['learning_hours']:.1f}h this week"
        )
    
    col4, col5 = st.columns(2)
    
    with col4:
        st.metric(
            label="Completion Rate", 
            value=f"{stats['completion_rate']}%",
            delta=f"{weekly_stats['completion_rate']:+.0f}% this week"
        )
    
    with col5:
        st.metric(
            label="Knowledge Score", 
            value=stats['knowledge_score'],
            delta=f"+{weekly_stats['knowledge_score']} points"
        )

def calculate_nodes_created(db, user_id, days=None):
    """Calculate total nodes created by user"""
    query = {"user_id": user_id}
    
    # Add date filter if specified
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query["created_at"] = {"$gte": cutoff_date}
    
    # Count nodes across all trees
    trees = db.knowledge_trees.find(query)
    node_count = 0
    
    for tree in trees:
        nodes = tree.get('nodes', [])
        node_count += len(nodes)
    
    return node_count

def calculate_connections(db, user_id, days=None):
    """Calculate total connections (edges) created by user"""
    query = {"user_id": user_id}
    
    # Add date filter if specified
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query["created_at"] = {"$gte": cutoff_date}
    
    # Count edges across all trees
    trees = db.knowledge_trees.find(query)
    edge_count = 0
    
    for tree in trees:
        edges = tree.get('edges', [])
        edge_count += len(edges)
    
    return edge_count

def calculate_learning_hours(db, user_id, days=None):
    """Calculate total learning hours from sessions"""
    query = {"user_id": user_id}
    
    # Add date filter if specified
    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query["timestamp"] = {"$gte": cutoff_date}
    
    # Sum time spent across sessions (convert seconds to hours)
    sessions = db.learning_sessions.find(query)
    total_seconds = 0
    
    for session in sessions:
        total_seconds += session.get('time_spent', 0)
    
    return total_seconds / 3600  # Convert to hours

def calculate_completion_rate(db, user_id):
    """Calculate completion rate based on sessions"""
    # This is a placeholder implementation
    # In a real system, you'd track completed vs started learning objectives
    return 75  # Placeholder percentage

def calculate_weekly_completion_delta(db, user_id):
    """Calculate change in completion rate this week"""
    # This is a placeholder implementation
    # In a real system, you'd compare current week to previous week
    return 5  # Placeholder percentage change

def calculate_knowledge_score(db, user_id):
    """Calculate knowledge score based on nodes, connections and sessions"""
    # Simple scoring algorithm:
    # (Nodes * 10) + (Connections * 5) + (Learning Hours * 20)
    nodes = calculate_nodes_created(db, user_id)
    connections = calculate_connections(db, user_id)
    hours = calculate_learning_hours(db, user_id)
    
    return int(nodes * 10 + connections * 5 + hours * 20)

def calculate_weekly_score_delta(db, user_id):
    """Calculate change in knowledge score this week"""
    # Simple implementation: just calculate points earned this week
    nodes_this_week = calculate_nodes_created(db, user_id, days=7)
    connections_this_week = calculate_connections(db, user_id, days=7)
    hours_this_week = calculate_learning_hours(db, user_id, days=7)
    
    return int(nodes_this_week * 10 + connections_this_week * 5 + hours_this_week * 20)

def show_activity_chart(db, user_id):
    """Show a timeline of learning activity from database"""
    # Get learning sessions for the last 14 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=14)
    
    sessions = db.learning_sessions.find({
        "user_id": user_id,
        "timestamp": {"$gte": start_date, "$lte": end_date}
    }).sort("timestamp", 1)
    
    # Create a date range for all 14 days
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Initialize data with zeros
    daily_minutes = {date.strftime('%Y-%m-%d'): 0 for date in date_range}
    
    # Populate with actual data
    for session in sessions:
        session_date = session.get('timestamp').strftime('%Y-%m-%d')
        daily_minutes[session_date] = daily_minutes.get(session_date, 0) + (session.get('time_spent', 0) / 60)
    
    # Create DataFrame
    activity_data = pd.DataFrame({
        'Date': list(daily_minutes.keys()),
        'Minutes': list(daily_minutes.values())
    })
    
    # Calculate weekly total
    weekly_total = sum(list(daily_minutes.values())[-7:])
    
    # Display weekly total
    st.markdown(f"**Weekly Learning:** {weekly_total:.0f} minutes")
    
    # Create activity chart
    fig = px.bar(
        activity_data, 
        x='Date', 
        y='Minutes',
        title='Daily Learning Activity',
        labels={'Date': '', 'Minutes': 'Minutes Spent Learning'},
        color='Minutes',
        color_continuous_scale='purples'
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#f0f0f0',
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        coloraxis_showscale=False
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_topic_distribution(db, user_id):
    """Show distribution of learning across topics from database"""
    # Get all knowledge trees
    trees = list(db.knowledge_trees.find({"user_id": user_id}))
    
    if not trees:
        st.info("No learning data available yet. Start creating knowledge trees!")
        return
    
    # Get learning sessions to determine time spent per topic
    sessions = list(db.learning_sessions.find({"user_id": user_id}))
    
    # Calculate time spent per topic
    topic_times = {}
    for session in sessions:
        topic = session.get('topic', 'Other')
        time_hours = session.get('time_spent', 0) / 3600  # Convert seconds to hours
        topic_times[topic] = topic_times.get(topic, 0) + time_hours
    
    # Prepare data for chart
    topics = list(topic_times.keys())
    hours = list(topic_times.values())
    
    # If no session data, use tree counts instead
    if not topic_times:
        topic_counts = {}
        for tree in trees:
            topic = tree.get('topic', 'Other')
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        topics = list(topic_counts.keys())
        hours = list(topic_counts.values())
    
    # Create pie chart
    fig = px.pie(
        values=hours,
        names=topics,
        title='Topic Distribution',
        color_discrete_sequence=px.colors.sequential.Purples_r
    )
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#f0f0f0',
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def show_mini_knowledge_graph(db, user_id):
    """Show a compact representation of the knowledge graph"""
    # Get the most recently updated knowledge tree
    tree = db.knowledge_trees.find_one(
        {"user_id": user_id},
        sort=[("updated_at", -1)]
    )
    
    if not tree:
        st.info("No knowledge trees available yet. Start creating one!")
        return
    
    # Extract nodes and edges
    nodes = tree.get('nodes', [])
    edges = tree.get('edges', [])
    topic = tree.get('topic', 'Unknown Topic')
    
    # If too many nodes, limit to most important ones
    if len(nodes) > 10:
        # Sort by connections or other importance metric
        # For now, just take first 10
        nodes = nodes[:10]
        
        # Filter edges to only include selected nodes
        node_ids = [node.get('id') for node in nodes]
        edges = [edge for edge in edges if edge.get('source') in node_ids and edge.get('target') in node_ids]
    
    # Create network graph
    st.markdown(f"**Preview of '{topic}' Knowledge Tree**")
    
    # Create position data for nodes (in a circle layout for simplicity)
    n = len(nodes)
    radius = 5
    angle_step = 2 * np.pi / n if n > 0 else 0
    
    node_positions = {}
    for i, node in enumerate(nodes):
        node_id = node.get('id')
        angle = i * angle_step
        x = radius * np.cos(angle) + 5  # Center at (5,5)
        y = radius * np.sin(angle) + 5
        node_positions[node_id] = (x, y)
    
    # Create scatter plot for nodes
    node_x = [pos[0] for pos in node_positions.values()]
    node_y = [pos[1] for pos in node_positions.values()]
    node_text = [node.get('label', 'Node') for node in nodes]
    node_size = [20 + len(node.get('label', '')) for node in nodes]  # Size based on label length
    
    fig = go.Figure()
    
    # Add edges as lines
    for edge in edges:
        source_id = edge.get('source')
        target_id = edge.get('target')
        
        if source_id in node_positions and target_id in node_positions:
            source_pos = node_positions[source_id]
            target_pos = node_positions[target_id]
            
            fig.add_trace(
                go.Scatter(
                    x=[source_pos[0], target_pos[0]],
                    y=[source_pos[1], target_pos[1]],
                    mode='lines',
                    line=dict(width=1.5, color='rgba(124, 77, 255, 0.6)'),
                    hoverinfo='none',
                    showlegend=False
                )
            )
    
    # Add nodes
    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            marker=dict(
                size=node_size,
                color=list(range(len(nodes))),
                colorscale='Purples',
                line=dict(width=1, color='#f0f0f0')
            ),
            text=node_text,
            textposition="top center",
            hoverinfo='text',
            name='Nodes'
        )
    )
    
    fig.update_layout(
        title=f'Knowledge Network Preview: {topic}',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#f0f0f0',
        showlegend=False,
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Link to full visualizer
    st.button("View Full Knowledge Graph", key="view_full_graph", on_click=set_page, args=('visualizer',))

def show_recent_activity(db, user_id):
    """Show recent learning activity from database"""
    st.markdown("### 📝 Recent Activity")
    
    # Get recent sessions
    recent_sessions = list(db.learning_sessions.find(
        {"user_id": user_id}
    ).sort("timestamp", -1).limit(5))
    
    # Get recent tree updates
    recent_trees = list(db.knowledge_trees.find(
        {"user_id": user_id}
    ).sort("updated_at", -1).limit(5))
    
    # Combine and sort by timestamp
    activities = []
    
    for session in recent_sessions:
        activities.append({
            "type": "session",
            "title": f"Studied {session.get('topic', 'Unknown Topic')}",
            "time": format_time_ago(session.get('timestamp', datetime.utcnow())),
            "icon": "📚",
            "duration": f"{session.get('time_spent', 0) // 60} minutes"
        })
    
    for tree in recent_trees:
        activities.append({
            "type": "tree",
            "title": f"Updated {tree.get('topic', 'Unknown Topic')} tree",
            "time": format_time_ago(tree.get('updated_at', datetime.utcnow())),
            "icon": "🌳",
            "nodes": len(tree.get('nodes', []))
        })
    
    # Sort by time (most recent first)
    activities.sort(key=lambda x: parse_time_ago(x["time"]))
    
    if not activities:
        st.info("No recent activity. Start learning!")
        return
    
    # Display activities
    for activity in activities[:5]:  # Show top 5
        with st.container():
            cols = st.columns([1, 6, 2])
            with cols[0]:
                st.markdown(f"### {activity['icon']}")
            with cols[1]:
                st.markdown(f"**{activity['title']}**")
                if activity['type'] == 'session':
                    st.markdown(f"Duration: {activity['duration']}")
                else:
                    st.markdown(f"Nodes: {activity['nodes']}")
            with cols[2]:
                st.markdown(f"{activity['time']}")
            st.markdown("---")

def format_time_ago(timestamp):
    """Format timestamp as relative time (e.g., '2 hours ago')"""
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.days > 7:
        return timestamp.strftime("%b %d, %Y")
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

def parse_time_ago(time_ago):
    """Parse relative time for sorting (lower value = more recent)"""
    if "just now" in time_ago.lower():
        return 0
    elif "minute" in time_ago.lower():
        return int(time_ago.split()[0]) * 60
    elif "hour" in time_ago.lower():
        return int(time_ago.split()[0]) * 3600
    elif "day" in time_ago.lower():
        return int(time_ago.split()[0]) * 86400
    elif "," in time_ago:  # Date format
        try:
            dt = datetime.strptime(time_ago, "%b %d, %Y")
            now = datetime.utcnow()
            return (now - dt).total_seconds()
        except:
            return 999999999
    return 999999999  # Default for unknown formats

def show_recommendations(db, user_id):
    """Show personalized learning recommendations"""
    st.markdown("### 🔍 Recommendations")
    
    # Get user's knowledge trees
    trees = list(db.knowledge_trees.find({"user_id": user_id}))
    
    if not trees:
        st.info("Start creating knowledge trees to get personalized recommendations!")
        return
    
    # Extract topics
    topics = [tree.get('topic', '') for tree in trees]
    
    # Generate recommendations based on existing topics
    # This is a simplified approach. In a real system, you would use more sophisticated methods.
    recommendations = generate_recommendations(topics)
    
    # Display recommendations
    for i, rec in enumerate(recommendations[:3]):
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"### {rec['icon']}")
            with col2:
                st.markdown(f"**{rec['title']}**")
                st.markdown(rec['description'])
            
            # Action buttons
            st.button(f"Explore {rec['title']}", key=f"explore_rec_{i}")
            st.markdown("---")

def generate_recommendations(topics):
    """Generate learning recommendations based on user's topics"""
    # This is a simplified recommendation system
    # In a real system, you would use machine learning or more sophisticated methods
    
    recommendations = []
    
    # Check for common topics and suggest related areas
    if any('machine learning' in topic.lower() for topic in topics):
        recommendations.append({
            "icon": "🤖",
            "title": "Deep Learning Fundamentals",
            "description": "Expand your machine learning knowledge with neural networks and deep learning concepts."
        })
    
    if any('python' in topic.lower() for topic in topics):
        recommendations.append({
            "icon": "🐍",
            "title": "Advanced Python Techniques",
            "description": "Learn about decorators, metaclasses, and optimizing Python code."
        })
    
    if any('data' in topic.lower() for topic in topics):
        recommendations.append({
            "icon": "📊",
            "title": "Data Visualization Mastery",
            "description": "Create compelling visualizations to communicate insights from your data."
        })
    
    # Add some general recommendations if we don't have enough
    general_recommendations = [
        {
            "icon": "🧠",
            "title": "Cognitive Science Basics",
            "description": "Understand how learning works in the brain to optimize your study techniques."
        },
        {
            "icon": "📱",
            "title": "Mobile App Development",
            "description": "Build cross-platform mobile applications using modern frameworks."
        },
        {
            "icon": "🔐",
            "title": "Cybersecurity Fundamentals",
            "description": "Learn essential practices to secure applications and protect data."
        },
        {
            "icon": "🌐",
            "title": "Web Development Pathway",
            "description": "From HTML/CSS basics to advanced JavaScript frameworks."
        }
    ]
    
    # Add general recommendations if we need more
    while len(recommendations) < 3:
        if not general_recommendations:
            break
        # Take a random recommendation to add variety
        import random
        rec = random.choice(general_recommendations)
        general_recommendations.remove(rec)
        recommendations.append(rec)
    
    return recommendations

def set_page(page):
    """Set current page in session state"""
    st.session_state.current_page = page