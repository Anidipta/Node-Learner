import streamlit as st
from utils import get_base64_image

def show_landing(authenticated=False):
    """Display an enhanced landing page with smooth animations and improved UI for NodeLearn"""
    
    # CSS for animations and styling - with toned down colors
    st.markdown("""
    <style>
        /* Base styles */
        body {
            background-color: #0a0a0a;
            color: #f0f0f0;
            font-family: 'Inter', sans-serif;
        }
        
        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes glow {
            0% { box-shadow: 0 0 5px rgba(156, 39, 176, 0.4); }
            50% { box-shadow: 0 0 15px rgba(156, 39, 176, 0.6), 0 0 20px rgba(224, 64, 251, 0.4); }
            100% { box-shadow: 0 0 5px rgba(156, 39, 176, 0.4); }
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.03); }
            100% { transform: scale(1); }
        }
        
        /* Component styles */
        .main-header {
            font-size: 3.5rem !important;
            font-weight: 800 !important;
            background: linear-gradient(45deg, #9c27b0, #d158e9, #7c4dff);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            margin-bottom: 0.5rem;
            animation: fadeIn 1s ease-out;
            text-align: center;
        }
        
        .sub-header {
            font-size: 1.6rem !important;
            color: #b39ddb;
            margin-bottom: 3rem;
            opacity: 0.9;
            animation: fadeIn 1.2s ease-out;
            text-align: center;
        }
        
        .section-header {
            font-size: 2rem !important;
            font-weight: 700 !important;
            color: #d158e9;
            margin: 2.5rem 0 1.5rem 0;
            animation: fadeIn 1.4s ease-out;
        }
        
        .node-card {
            background-color: rgba(25, 25, 30, 0.7);
            border-radius: 12px;
            border: 1px solid #7c4dff;
            box-shadow: 0 4px 8px rgba(156, 39, 176, 0.2);
            padding: 22px;
            margin-bottom: 22px;
            transition: all 0.3s ease;
            animation: fadeIn 1.6s ease-out;
        }
        
        .node-card:hover {
            transform: translateY(-3px);
            border-color: #d158e9;
            box-shadow: 0 6px 14px rgba(224, 64, 251, 0.3);
        }
        
        .node-card h3 {
            color: #e1bee7;
            font-size: 1.4rem;
            margin-bottom: 12px;
        }
        
        .node-card p {
            color: #d1c4e9;
            font-size: 1.05rem;
            line-height: 1.5;
        }
        
        .hero-section {
            padding: 2.5rem 1rem;
            text-align: center;
            background: linear-gradient(135deg, rgba(20,20,25,0.8) 0%, rgba(60,20,80,0.3) 100%);
            border-radius: 16px;
            margin-bottom: 2.5rem;
            animation: fadeIn 1s ease-out;
        }
        
        .cta-button {
            background: linear-gradient(45deg, #9c27b0, #7c4dff) !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 0.7rem 1.8rem !important;
            border-radius: 50px !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(124, 77, 255, 0.4) !important;
            transition: all 0.3s ease !important;
            margin-top: 1rem !important;
        }
        
        .cta-button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(224, 64, 251, 0.5) !important;
        }
        
        .feature-icon {
            font-size: 2.2rem;
            margin-bottom: 0.8rem;
            color: #d158e9;
        }
        
        .tech-badge {
            display: inline-block;
            background-color: rgba(40, 40, 50, 0.7);
            border: 1px solid #7c4dff;
            border-radius: 50px;
            padding: 0.5rem 1.3rem;
            margin: 0.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .tech-badge:hover {
            background-color: rgba(124, 77, 255, 0.15);
            transform: translateY(-2px);
        }
        
        .step-container {
            background-color: rgba(25, 25, 30, 0.5);
            border-left: 3px solid #d158e9;
            padding: 0.5rem;
            margin-bottom: 1.2 rem;
            border-radius: 0 8px 8px 0;
            transition: all 0.3s ease;
        }
        
        .step-container:hover {
            background-color: rgba(40, 40, 50, 0.6);
            border-left-width: 4px;
        }
        
        .step-number {
            font-size: 1.8rem;
            font-weight: 700;
            color: #d158e9;
            margin-right: 2.0rem;
        }
        
        /* Custom scroll behavior */
        html {
            scroll-behavior: smooth;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #0a0a0a;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #7c4dff;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #d158e9;
        }
        
        /* Testimonial section */
        .testimonial {
            background: linear-gradient(135deg, rgba(25,25,30,0.7) 0%, rgba(60,20,80,0.2) 100%);
            border-radius: 12px;
            padding: 1.8rem;
            margin: 1rem 0;
            position: relative;
        }
        
        .testimonial-quote {
            font-size: 1.1rem;
            font-style: italic;
            color: #e1bee7;
            line-height: 1.5;
        }
        
        .testimonial-author {
            font-weight: 600;
            color: #b39ddb;
            margin-top: 1rem;
            text-align: right;
        }
        
        /* Stats counter */
        .stats-counter {
            text-align: center;
            padding: 1.8rem 0;
        }
        
        .counter-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: #d158e9;
            margin-bottom: 0.5rem;
        }
        
        .counter-label {
            font-size: 1.1rem;
            color: #b39ddb;
        }
        
        /* Footer */
        .footer {
            margin-top: 3rem;
            padding: 1.5rem 0;
            text-align: center;
            color: #9575cd;
            font-size: 0.9rem;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .main-header {
                font-size: 2.8rem !important;
            }
            
            .sub-header {
                font-size: 1.4rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Logo and Hero Section
    with st.container():
        col1, col2, col3 = st.columns([1, 10, 1])
        with col2:
            logo_base64 = get_base64_image("assets/logo_design.png")
            st.markdown(
                f"<h1 class='main-header'><img src='{logo_base64}' width='90' style='vertical-align:middle; margin-right:10px;'> NodeLearn</h1>", 
                unsafe_allow_html=True
            )


            st.markdown("<p class='sub-header'>Transform your learning journey with interactive knowledge visualization</p>", 
                        unsafe_allow_html=True)
            
            # Different CTAs based on authentication status
            if not authenticated:
                col_a, col_b, col_c = st.columns([1, 1, 1])
                with col_a:
                    if st.button("✨ Connect with Google", key="demo_button", use_container_width=True):
                        st.session_state.current_page = 'signup'
                        st.rerun()
                with col_b:
                    if st.button("🔑 Login", key="login_button", use_container_width=True):
                        st.session_state.current_page = 'login'
                        st.rerun()
                with col_c:
                    if st.button("📝 Sign Up", key="signup_button", use_container_width=True):
                        st.session_state.current_page = 'signup'
                        st.rerun()
            else:
                # Personalized welcome for authenticated users
                st.markdown(f"<h3 style='color:#b39ddb;'>Welcome back, {st.session_state.get('username', 'Explorer')}!</h3>", unsafe_allow_html=True)
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    if st.button("🌳 Continue Learning", key="continue_button", use_container_width=True):
                        st.session_state.current_page = 'visualizer'
                        st.rerun()
                with col_b:
                    if st.button("📚 View History", key="history_button", use_container_width=True):
                        st.session_state.current_page = 'history'
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    
    # What is NodeLearn section with static image instead of Lottie
    st.markdown("<h2 class='section-header'>🌟 Reimagine How You Learn</h2>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style='animation: fadeIn 1.4s ease-out;'>
            <p style='font-size: 2.0rem; line-height: 3.0; color: #d1c4e9;'>
                <b>NodeLearn</b> revolutionizes education by transforming complex topics into <span style='color: #d158e9;'>interactive visual knowledge trees</span>.
            </p>
            <p style='font-size: 1.15rem; line-height: 1.7; color: #d1c4e9; margin-top: 1rem;'>
                Unlike traditional linear learning methods, our platform allows you to:
            </p>
            <ul style='font-size: 1.15rem; line-height: 2.2; color: #d1c4e9;'>
                <li>Visualize connections between related concepts</li>
                <li>Navigate complex topics at your own pace</li>
                <li>Build a personalized knowledge map powered by AI</li>
                <li>Discover new paths of exploration based on your interests</li>
            </ul>
            <p style='font-size: 1.75rem; line-height: 2.5; color: #d1c4e9; margin-top: 1.5rem; margin-left: 2.0rem ;align: center;'>
                The future of learning is <span style='color: #d158e9;'>interconnected</span>, <span style='color: #7c4dff;'>visual</span>, and <span style='color: #9c27b0;'>personalized</span>.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Key stats section (for visual impact)
    st.markdown("<h2 class='section-header'>🔢 NodeLearn Impact</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='stats-counter'>
            <div class='counter-value'>10,000+</div>
            <div class='counter-label'>Knowledge Trees Created</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='stats-counter'>
            <div class='counter-value'>85%</div>
            <div class='counter-label'>Increase in Learning Retention</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='stats-counter'>
            <div class='counter-value'>50+</div>
            <div class='counter-label'>Academic Disciplines Mapped</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Features section with enhanced cards
    st.markdown("<h2 class='section-header'>✨ Key Features</h2>", unsafe_allow_html=True)
    
    features = [
        {
            "icon": "🌳",
            "title": "Interactive Knowledge Trees",
            "description": "Visualize concepts as expandable trees with intuitive navigation. Click on any node to explore deeper and discover related ideas."
        },
        {
            "icon": "🤖",
            "title": "AI-Powered Exploration",
            "description": "Our intelligent system suggests personalized learning paths and related concepts based on your interests and learning history."
        },
        {
            "icon": "✨",
            "title": "Stunning Visualizations",
            "description": "Experience your knowledge journey through beautiful, responsive visuals with smooth transitions and intuitive interactions."
        },
        {
            "icon": "🧠",
            "title": "Learning Analytics",
            "description": "Track your progress with detailed insights and analysis about your learning patterns, strengths, and areas for exploration."
        },
    ]
    
    # Display features in a 2x2 grid with enhanced styling
    col1, col2 = st.columns(2)
    
    for i, feature in enumerate(features):
        with col1 if i % 2 == 0 else col2:
            with st.container():
                st.markdown(f"""
                <div class="node-card">
                    <div class="feature-icon">{feature['icon']}</div>
                    <h3>{feature['title']}</h3>
                    <p>{feature['description']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # How it works section with step-by-step visualization
    st.markdown("<h2 class='section-header'>🧩 How NodeLearn Works</h2>", unsafe_allow_html=True)
    
    steps = [
        {
            "title": "Start With A Topic",
            "description": "Begin your journey by entering any subject you're curious about – from quantum physics to medieval history."
        },
        {
            "title": "Explore The Knowledge Tree",
            "description": "Watch as your topic expands into a network of connected concepts. Click on any node to dive deeper into specific areas."
        },
        {
            "title": "Learn With AI Assistance",
            "description": "Our AI provides concise explanations, suggests relevant resources, and helps you understand complex relationships between ideas."
        },
        {
            "title": "Track Your Progress",
            "description": "Your knowledge map is saved automatically. Return anytime to continue exploring or review your learning journey."
        }
    ]
    
    for i, step in enumerate(steps):
        st.markdown(f"""
        <div class="step-container">
            <div style="display: flex; align-items: center;">
                <span class="step-number">{i+1}</span>
                <div>
                    <h3 style="color: #e1bee7; margin-bottom: 0.5rem;">{step['title']}</h3>
                    <p style="color: #d1c4e9; font-size: 1.05rem;">{step['description']}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Testimonial section (adds social proof)
    if not authenticated:
        st.markdown("<h2 class='section-header'>❤️ What Our Users Say</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="testimonial">
                <div class="testimonial-quote">
                    "NodeLearn completely changed how I approach complex subjects. The visual mapping helped me understand the connections in molecular biology that I was missing with traditional notes."
                </div>
                <div class="testimonial-author">- Sarah K., Graduate Student</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class="testimonial">
                <div class="testimonial-quote">
                    "As an educator, I've seen my students' comprehension improve dramatically since integrating NodeLearn into our curriculum. The visual approach helps different learning styles."
                </div>
                <div class="testimonial-author">- Professor James T., Computer Science</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Technologies section with badges
    st.markdown("<h2 class='section-header'>🛠️ Built With Cutting-Edge Tech</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0; animation: fadeIn 1.8s ease-out;">
        <span class="tech-badge">🐍 Python</span>
        <span class="tech-badge">🖥️ Streamlit</span>
        <span class="tech-badge">🧠 GenAI</span>
        <span class="tech-badge">🗄️ MongoDB</span>
        <span class="tech-badge">📊 NetworkX</span>
        <span class="tech-badge">🔄 Plotly</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Call to action section
    st.markdown("<h2 class='section-header'>🚀 Ready to Transform Your Learning?</h2>", unsafe_allow_html=True)
    
    # Different CTA based on authentication status
    if not authenticated:
        if st.button("Get Started Now", key="cta_button", use_container_width=True):
                st.session_state.current_page = 'signup'
                st.rerun()
    else:
        if st.button("Continue Your Learning Journey", key="continue_journey", use_container_width=True):
                st.session_state.current_page = 'visualizer'
                st.rerun()
    
    # Footer section
    st.markdown("""
    <div class="footer">
        <p>© 2025 NodeLearn | Privacy Policy | Terms of Service</p>
        <p>Made with 💜 for curious minds everywhere</p>
    </div>
    """, unsafe_allow_html=True)