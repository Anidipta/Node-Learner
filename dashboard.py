import streamlit as st
import pandas as pd
import random
from db import get_db_connection
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

def show_dashboard():
    """Display the user dashboard with personalized statistics and account settings"""
    
    # Dashboard CSS styling
    st.markdown("""
    <style>
        /* Dashboard specific styling */
        .dashboard-header {
            font-size: 2.2rem;
            font-weight: 700;
            background: linear-gradient(45deg, #9c27b0, #7c4dff);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            margin-bottom: 1.5rem;
        }
        
        .dashboard-card {
            background-color: rgba(25, 25, 35, 0.7);
            border-radius: 12px;
            border: 1px solid rgba(124, 77, 255, 0.3);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            transition: all 0.3s ease;
        }
        
        .dashboard-card:hover {
            border-color: rgba(209, 88, 233, 0.5);
            box-shadow: 0 4px 12px rgba(156, 39, 176, 0.2);
        }
        
        .stat-card {
            background: linear-gradient(135deg, rgba(25,25,35,0.8) 0%, rgba(40,20,60,0.4) 100%);
            border-radius: 10px;
            padding: 1.2rem;
            text-align: center;
            transition: all 0.3s ease;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 14px rgba(124, 77, 255, 0.2);
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #d158e9;
            margin-bottom: 0.5rem;
        }
        
        .stat-label {
            color: #b39ddb;
            font-size: 1rem;
        }
        
        .tab-content {
            padding: 1.5rem 0;
        }
        
        .user-avatar {
            border-radius: 50%;
            border: 3px solid #7c4dff;
            padding: 3px;
        }
        
        .profile-header {
            display: flex;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        
        .profile-info {
            margin-left: 1.5rem;
        }
        
        .profile-name {
            font-size: 1.8rem;
            font-weight: 700;
            color: #e1bee7;
            margin-bottom: 0.3rem;
        }
        
        .profile-email {
            color: #b39ddb;
            font-size: 1rem;
        }
        
        .settings-section {
            margin-bottom: 2rem;
        }
        
        .settings-header {
            font-size: 1.3rem;
            font-weight: 600;
            color: #d158e9;
            margin-bottom: 1rem;
            border-bottom: 1px solid rgba(124, 77, 255, 0.3);
            padding-bottom: 0.5rem;
        }
        
        /* Form styling */
        .stTextInput input, .stNumberInput input, .stSelectbox select {
            background-color: rgba(30, 30, 40, 0.6) !important;
            color: #e1bee7 !important;
            border: 2px solid rgba(124, 77, 255, 0.3) !important;
            border-radius: 8px !important;
        }
        
        .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
            border-color: #d158e9 !important;
            box-shadow: 0 0 0 2px rgba(209, 88, 233, 0.2) !important;
        }
        
        /* Custom alert */
        .custom-alert {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            display: flex;
            align-items: center;
        }
        
        .alert-success {
            background-color: rgba(76, 175, 80, 0.1);
            border-left: 4px solid #4CAF50;
        }
        
        .alert-info {
            background-color: rgba(33, 150, 243, 0.1);
            border-left: 4px solid #2196F3;
        }
        
        .alert-warning {
            background-color: rgba(255, 152, 0, 0.1);
            border-left: 4px solid #FF9800;
        }
        
        .alert-icon {
            margin-right: 0.8rem;
            font-size: 1.5rem;
        }
        
        .alert-message {
            color: #e1bee7;
        }
    </style>
    """, unsafe_allow_html=True)

    db = get_db_connection()
    user_name = st.session_state.get('user_name', 'Explorer')
    user = db.users.find_one({"name": user_name})
    user_id = user.get("_id", '')
    user_email = user.get("email", '')
    join_date = user.get("created_at", '2025-01-01')
    knowledge_trees = db.knowledge_trees.find({"user_id": user_id})
    learning_sessions = db.learning_sessions.find({"user_id": user_id})
    time_spent = sum([session.get("time_spent", 0) for session in learning_sessions])
    
    
    # Page header
    st.markdown(f"<h1 class='dashboard-header'>Welcome , {user_name} </h1>", unsafe_allow_html=True)
   
    # Dashboard tabs
    st.markdown("""
        <style>
            .stTabs [data-baseweb="tab"] {
                font-size: 2.5rem; 
                width: 100%;
                justify-content: center;
            }
            .stTabs [data-baseweb="tab-list"] {
                display: flex;
                width: 100%;
            }
        </style>
    """, unsafe_allow_html=True)
    
    tab1, tab2= st.tabs(["📊 Overview", "👤 Profile Settings"])
    
    with tab1:
        st.markdown("<div class='tab-content'>", unsafe_allow_html=True)
        
        # User activity summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{db.get_learning_stats(st.session_state.user_id).get("total_sessions", 0)}</div>
                <div class="stat-label">Knowledge Trees</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{db.get_learning_stats(st.session_state.user_id).get("topics_explored", 0)}</div>
                <div class="stat-label">Topics Explored</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-value">{db.get_learning_stats(st.session_state.user_id).get("total_time", 0)/60:.2f} min </div>
                <div class="stat-label">Learning Time</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent activity
        st.subheader("Activities")    
        col_a, col_b = st.columns([1, 1])
        with col_a:
            if st.button("🌳 Continue Learning", key="continue_button", use_container_width=True):
                st.session_state.current_page = 'visualizer'
                st.rerun()
        with col_b:
            if st.button("📚 View History", key="history_button", use_container_width=True):
                st.session_state.current_page = 'history'
                st.rerun()    
                
        # Recent learning sessions chart
        learning_data = list(learning_sessions)
        if learning_data:
            st.markdown("<h3 class='settings-header'>📈 Recent Learning Sessions</h3>", unsafe_allow_html=True)
            df = pd.DataFrame(learning_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['time_spent'] = df['time_spent'].apply(lambda x: x // 60)
            df = df.sort_values(by='timestamp', ascending=False).head(10)
            fig = px.bar(df, x='timestamp', y='time_spent', color='topic', title="Recent Learning Sessions", text='time_spent')
            fig.update_traces(texttemplate='%{text} min', textposition='outside')
            fig.update_layout(title_x=0.5, title_font=dict(size=24), xaxis_title="Date", yaxis_title="Time Spent (min)", height=400)
            st.plotly_chart(fig, use_container_width=True)
        
    with tab2:
        st.markdown("<div class='tab-content'>", unsafe_allow_html=True)
        
        # Profile header with avatar and basic info
        st.markdown(f"""
            <style>
                .profile-header {{
                    display: flex;
                    align-items: center;
                    background: linear-gradient(to right, #ede7f6, #d1c4e9);
                    padding: 1.5rem;
                    border-radius: 15px;
                    width: 100%;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
                    margin-bottom: 1.5rem;
                }}
                .user-avatar {{
                    border-radius: 50%;
                    border: 3px solid #9575cd;
                    margin-right: 1.5rem;
                    background-color: #000000;
                }}
                .profile-info {{
                    display: flex;
                    flex-direction: column;
                }}
                .profile-name {{
                    font-size: 1.6rem;
                    font-weight: bold;
                    color: #512da8;
                }}
                .profile-email {{
                    font-size: 1.1rem;
                    color: #5e35b1;
                }}
            </style>

            <div class="profile-header">
                <img src="https://api.dicebear.com/7.x/personas/svg?seed={user_name}" width="110" height="110" class="user-avatar">
                <div class="profile-info">
                    <div class="profile-name">{user_name}</div>
                    <div class="profile-email">{user_email}</div>
                    <div style="color: #7e57c2; margin-top: 0.5rem;">Member since: {str(join_date)[:10]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
          
        st.markdown("<h3 class='settings-header'>🔐 Password Settings</h3>", unsafe_allow_html=True)
        
        # Password change form
        with st.form("password_change_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            password_submitted = st.form_submit_button("Change Password", use_container_width=True)
            
            if password_submitted:
                if not current_password or not new_password or not confirm_password:
                    st.markdown("""
                    <div class="custom-alert alert-warning">
                        <span class="alert-icon">⚠️</span>
                        <span class="alert-message">Please fill in all password fields.</span>
                    </div>
                    """, unsafe_allow_html=True)
                elif new_password != confirm_password:
                    st.markdown("""
                    <div class="custom-alert alert-warning">
                        <span class="alert-icon">⚠️</span>
                        <span class="alert-message">New passwords do not match. Please try again.</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="custom-alert alert-success">
                        <span class="alert-icon">✅</span>
                        <span class="alert-message">Password changed successfully!</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Email notification settings section
        st.markdown("<div class='settings-section'>", unsafe_allow_html=True)
        st.markdown("<h3 class='settings-header'>📧 Email Settings</h3>", unsafe_allow_html=True)
        
        # Email change form
        with st.form("email_change_form"):
            new_email = st.text_input("New Email Address", value=user_email)
            confirm_email = st.text_input("Confirm New Email")
            password_verification = st.text_input("Password", type="password")
            
            email_submitted = st.form_submit_button("Update Email", use_container_width=True)
            
            if email_submitted:
                if not new_email or not confirm_email or not password_verification:
                    st.markdown("""
                    <div class="custom-alert alert-warning">
                        <span class="alert-icon">⚠️</span>
                        <span class="alert-message">Please fill in all email fields.</span>
                    </div>
                    """, unsafe_allow_html=True)
                elif new_email != confirm_email:
                    st.markdown("""
                    <div class="custom-alert alert-warning">
                        <span class="alert-icon">⚠️</span>
                        <span class="alert-message">Email addresses do not match. Please try again.</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="custom-alert alert-info">
                        <span class="alert-icon">ℹ️</span>
                        <span class="alert-message">A verification link has been sent to your new email address. Please check your inbox to complete the update.</span>
                    </div>
                    """, unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
                    # Clear all session state on logout
                    for key in list(st.session_state.keys()):
                        if key != 'current_page':
                            del st.session_state[key]
                    st.session_state.authenticated = False
                    st.session_state.current_page = 'landing'
                    st.session_state.show_sidebar = False  # Hide sidebar on logout
                    st.rerun()
                    
        st.markdown("</div>", unsafe_allow_html=True)
        