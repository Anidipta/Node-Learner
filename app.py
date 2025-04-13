import streamlit as st
from landing import show_landing
from auth import login_page, signup_page, is_authenticated
from visualizer import show_visualizer
from history import show_history

# Configure the page with initial sidebar hidden
st.set_page_config(
    page_title="NodeLearn",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"  # Start with sidebar collapsed
)

# App state management
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'
if 'show_sidebar' not in st.session_state:
    st.session_state.show_sidebar = False  # Initially hide sidebar for landing page

# Global CSS with simpler styling
st.markdown("""
<style>
    /* Base Theme */
    body {
        background-color: #0a0a0a;
        color: #f0f0f0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Custom scroll behavior */
    html {
        scroll-behavior: smooth;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a1a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #7c4dff;
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #d158e9;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(45deg, #9c27b0, #7c4dff) !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 2px 8px rgba(124, 77, 255, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    
    /* Button hover effect */
    .stButton>button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(224, 64, 251, 0.5) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-1wrcr25 {
        background-image: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Navigation items */
    .nav-item {
        background-color: rgba(30, 30, 40, 0.7);
        border-radius: 8px;
        padding: 8px 12px;
        margin: 4px 0;
        transition: all 0.3s ease;
        border-left: 2px solid transparent;
    }
    
    .nav-item:hover {
        background-color: rgba(156, 39, 176, 0.2);
        border-left: 2px solid #d158e9;
    }
    
    /* Active navigation item */
    .nav-item.active {
        background-color: rgba(156, 39, 176, 0.3);
        border-left: 2px solid #d158e9;
    }
</style>
""", unsafe_allow_html=True)

# Simplified sidebar navigation
def sidebar_nav():
    # Only show sidebar after login or if explicitly enabled
    if st.session_state.authenticated or st.session_state.show_sidebar:
        with st.sidebar:
            # Logo
            st.image("assets/logo.png", width=150)
            
            # User info if authenticated
            if st.session_state.authenticated:
                st.markdown(f"### Welcome, {st.session_state.get('user_name', 'Explorer')}")
            
            # Navigation options
            st.markdown("---")
            
            # Home button
            if st.button("🏠 Home", key="nav_home", use_container_width=True):
                st.session_state.current_page = 'landing' if not st.session_state.authenticated else 'home'
                st.rerun()
            
            # Conditional navigation based on authentication
            if st.session_state.authenticated:
                # Knowledge Tree button
                if st.button("🌳 Knowledge Tree", key="nav_tree", use_container_width=True):
                    st.session_state.current_page = 'visualizer'
                    st.rerun()
                
                # Learning History button
                if st.button("📚 Learning History", key="nav_history", use_container_width=True):
                    st.session_state.current_page = 'history'
                    st.rerun()
                
                # Logout option
                st.markdown("---")
                if st.button("🚪 Logout", key="nav_logout", use_container_width=True):
                    st.session_state.authenticated = False
                    st.session_state.current_page = 'landing'
                    st.session_state.show_sidebar = False  # Hide sidebar on logout
                    st.rerun()
            else:
                # Login button for unauthenticated users
                if st.button("🔑 Login", key="nav_login", use_container_width=True):
                    st.session_state.current_page = 'login'
                    st.rerun()
                
                # Sign Up button
                if st.button("📝 Sign Up", key="nav_signup", use_container_width=True):
                    st.session_state.current_page = 'signup'
                    st.rerun()

# Main app routing with simplified navigation
def main():
    # Show simple header for sidebar toggle
       
    # Show sidebar based on state
    sidebar_nav()
    
    # Route to the appropriate page
    if st.session_state.current_page == 'landing':
        show_landing()
    elif st.session_state.current_page == 'login':
        st.session_state.show_sidebar = True  # Show sidebar on login page
        login_page()
    elif st.session_state.current_page == 'signup':
        st.session_state.show_sidebar = True  # Show sidebar on signup page
        signup_page()
    # Protected routes (require authentication)
    elif is_authenticated():
        st.session_state.show_sidebar = True  # Always show sidebar for authenticated users
        if st.session_state.current_page == 'home':
            show_landing(authenticated=True)
        elif st.session_state.current_page == 'visualizer':
            show_visualizer()
        elif st.session_state.current_page == 'history':
            show_history()
    else:
        # Redirect to login if trying to access protected routes without authentication
        st.session_state.current_page = 'login'
        st.session_state.show_sidebar = True  # Show sidebar on login page
        st.rerun()

if __name__ == "__main__":
    main()