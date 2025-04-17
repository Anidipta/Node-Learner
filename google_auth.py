import streamlit as st
from streamlit_oauth import OAuth2Component
import requests
import os
from dotenv import load_dotenv
from db import get_db_connection
import hashlib

# Load environment variables
load_dotenv()

# Get values from environment
AUTHORIZE_URL = os.environ.get('AUTHORIZE_URL', 'https://accounts.google.com/o/oauth2/auth')
TOKEN_URL = os.environ.get('TOKEN_URL', 'https://oauth2.googleapis.com/token')
REFRESH_TOKEN_URL = os.environ.get('REFRESH_TOKEN_URL', 'https://oauth2.googleapis.com/token')
REVOKE_TOKEN_URL = os.environ.get('REVOKE_TOKEN_URL', 'https://oauth2.googleapis.com/revoke')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')
SCOPE = os.environ.get('SCOPE', 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email')

def connect_google():
    """Handle Google OAuth authentication"""
    # Create OAuth2 instance
    oauth2 = OAuth2Component(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        authorize_endpoint=AUTHORIZE_URL,
        token_endpoint=TOKEN_URL,
        refresh_token_endpoint=REFRESH_TOKEN_URL,
        revoke_token_endpoint=REVOKE_TOKEN_URL
    )
    
    # Custom Header
    st.markdown("""
        <style> 
            .main-header {
                font-size: 2.8em;
                color: #4a4a4a;
                font-weight: 800;
                text-align: center;
                margin-bottom: 0.2em;
            }
            .main-header:hover {
                color: #d158e9;
            }
            .info-box {
                padding: 1.2em;
                border-radius: 10px;
                border-left: 6px solid #d158e9;
                margin-bottom: 1em;
            }
            .highlight {
                color: #d158e9;
                font-weight: 600;
            }
        </style>

        <h2 class='main-header'>🔐 Connect with Google</h2>
    """, unsafe_allow_html=True)

    # Privacy and Info Section
    st.markdown("""
    <div class='info-box'>
        <h4>🔒 Your Privacy Comes First</h4>
        <p>When you connect with Google, we only access your <span class='highlight'>email address</span> and <span class='highlight'>name</span> to personalize your experience. No other information—like contacts or documents—is accessed.</p>
        <p>Your data is stored securely and <strong>never</strong> shared with third parties.</p>
        <p>By continuing, you agree to NodeLearn's 
        <a href='https://example.com/terms' target='_blank'>Terms of Service</a> and 
        <a href='https://example.com/privacy' target='_blank'>Privacy Policy</a>.</p>
    </div>
    """, unsafe_allow_html=True)

    # Sign In Benefits
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 🌟 Why Sign In With Google?
        - 🚀 **Instant Access** to your learning dashboard
        - 🔐 **Password-Free** sign-in experience
        - 💫 **Personalized Recommendations** based on your interests
        - ⏱️ **Quick setup** — no long forms to fill
        """)

    with col2:
        st.markdown("""
        ### 🎁 What You'll Get
        - 📚 **Full Access** to all courses and materials
        - 📊 **Real-Time Progress Tracking** across devices
        - 🏆 **Achievement Badges** and shareable certificates
        - 🤝 **Priority Support** from our team
        """)

    st.markdown("---")
    
    # Handle authorization
    if 'google_token' not in st.session_state:
        result = oauth2.authorize_button("Connect with Google", REDIRECT_URI, SCOPE)
        
        # Back button to return to previous page
        if st.button("← Back", key="google_back_button"):
            st.session_state.current_page = 'login'
            st.rerun()
            
        if result and 'token' in result:
            st.session_state.google_token = result.get('token')
            st.rerun()
    else:
        # Use token to call Google People API
        access_token = st.session_state.google_token['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get("https://www.googleapis.com/oauth2/v1/userinfo", headers=headers)
        
        if response.status_code == 200:
            user_info = response.json()
            name = user_info.get("name")
            email = user_info.get("email")
            google_id = user_info.get("id")
            
            # Hash the Google ID to use as password
            hashed_id = hashlib.sha256(google_id.encode()).hexdigest()
            
            # Check if user exists in database
            db = get_db_connection()
            user = db.users.find_one({"email": email})
            
            if user:
                # User exists, update Google ID if necessary
                if user.get("google_id") != google_id:
                    db.users.update_one(
                        {"email": email},
                        {"$set": {
                            "google_id": google_id,
                            "password": hashed_id,
                            "is_verified": True,
                            "last_login": db.get_timestamp()
                        }}
                    )
            else:
                # Create new user
                new_user = {
                    "name": name,
                    "email": email,
                    "password": hashed_id,
                    "google_id": google_id,
                    "created_at": db.get_timestamp(),
                    "last_login": db.get_timestamp(),
                    "is_verified": True
                }
                db.users.insert_one(new_user)
                user = db.users.find_one({"email": email})
            
            # Set authenticated session
            st.session_state.authenticated = True
            st.session_state.user_id = str(user["_id"])
            st.session_state.user_name = name
            st.session_state.current_page = 'dashboard'
            st.rerun()
        else:
            st.error("Failed to fetch user info. Please try again.")
            
            if st.button("Try Again", key="google_retry"):
                del st.session_state.google_token
                st.rerun()