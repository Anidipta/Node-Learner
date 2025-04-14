import streamlit as st
import hashlib
import re
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from db import get_db_connection
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Email configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def is_authenticated():
    """Check if the user is authenticated"""
    return st.session_state.get("authenticated", False)

def validate_email(email):
    """Validate email format"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email)

def is_valid_email(email):
    """Enhanced email validation"""
    # Basic email validation using regex
    email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_pattern, email):
        return False
    
    # Check for common email domains and TLDs
    email_domains = ["gmail", "hotmail", "yahoo", "outlook"]
    email_tlds = [".com", ".in", ".org", ".edu", ".co.in"]
    
    domain_valid = any(domain in email.lower() for domain in email_domains)
    tld_valid = any(tld in email.lower() for tld in email_tlds)
    
    return domain_valid and tld_valid

def validate_password(password):
    """Validate password strength"""
    # At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

def hash_password(password):
    """Hash password for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    """Generate a random 4-digit OTP"""
    return random.randint(1000, 9999)

def send_otp(receiver_email, otp, name="User"):
    """Send OTP to the specified email address"""
    try:
        # Create the email content
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = "OTP Verification"
        
        # Email body
        body = f"""Dear {name},

Your OTP for verification is {otp}.

This OTP is valid for 10 minutes.

Regards,
Your Application Team"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to the SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        # Send the email
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, receiver_email, text)
        server.quit()
        
        return True
    except Exception as e:
        st.error(f"Error sending email: {str(e)}")
        return False

def verify_otp(entered_otp, stored_otp):
    """Verify if the entered OTP matches the stored OTP"""
    return str(entered_otp) == str(stored_otp)

def verify_otp_page():
    """Display OTP verification page"""
    st.markdown("<h1 class='main-header'>✅ Verify Your Email</h1>", unsafe_allow_html=True)
    
    email = st.session_state.get("email_for_verification", "")
    
    if not email:
        st.error("No email found for verification. Please sign up again.")
        if st.button("Go to Sign Up"):
            st.session_state.current_page = 'signup'
            st.rerun()
        return
    
    st.info(f"An OTP has been sent to {email}. Please check your inbox.")
    
    # OTP verification form
    with st.form("otp_form"):
        entered_otp = st.text_input("Enter 4-digit OTP", max_chars=4)
        submit_button = st.form_submit_button("Verify")
    
    # Handle form submission
    if submit_button:
        if not entered_otp or len(entered_otp) != 4:
            st.error("Please enter a valid 4-digit OTP")
            return
        
        # Verify OTP
        db = get_db_connection()
        user = db.users.find_one({"email": email})
        
        if not user:
            st.error("User not found. Please sign up again.")
            return
        
        # Check if OTP has expired
        current_time = time.time()
        if current_time > user.get("otp_expiry", 0):
            st.error("OTP has expired. Please request a new one.")
            if st.button("Resend OTP"):
                new_otp = generate_otp()
                db.users.update_one(
                    {"email": email},
                    {"$set": {
                        "otp": str(new_otp),
                        "otp_expiry": time.time() + 600  # 10 minutes
                    }}
                )
                if send_otp(email, new_otp, user["name"]):
                    st.success("New OTP sent successfully!")
                    st.rerun()
                else:
                    st.error("Failed to send OTP. Please try again.")
            return
        
        # Verify OTP
        if verify_otp(entered_otp, user["otp"]):
            # Mark user as verified
            db.users.update_one(
                {"email": email},
                {"$set": {
                    "is_verified": True,
                    "verified_at": db.get_timestamp()
                }}
            )
            
            # Auto login after verification
            st.session_state.authenticated = True
            st.session_state.user_id = str(user["_id"])
            st.session_state.user_name = user["name"]
            st.session_state.current_page = 'home'
            
            st.success("Email verified successfully!")
            st.rerun()
        else:
            st.error("Invalid OTP. Please try again.")
    
    # Option to resend OTP
    st.markdown("---")
    if st.button("Resend OTP"):
        new_otp = generate_otp()
        db = get_db_connection()
        user = db.users.find_one({"email": email})
        
        db.users.update_one(
            {"email": email},
            {"$set": {
                "otp": str(new_otp),
                "otp_expiry": time.time() + 600  # 10 minutes
            }}
        )
        
        if send_otp(email, new_otp, user["name"]):
            st.success("OTP resent successfully!")
        else:
            st.error("Failed to resend OTP. Please try again.")
            
            
def login_page():
    """Display login page and handle authentication"""
    st.markdown("<h1 class='main-header'>🔑 Login</h1>", unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
    
    # Handle form submission
    if submit_button:
        if not email or not password:
            st.error("Please enter both email and password")
            return
        
        # Validate email format
        if not validate_email(email):
            st.error("Please enter a valid email address")
            return
        
        # Hash password for comparison
        hashed_password = hash_password(password)
        
        # Check credentials in database
        db = get_db_connection()
        user = db.users.find_one({"email": email})
        
        if user and user["password"] == hashed_password:
            # Check if user is verified
            if not user.get("is_verified", False):
                st.warning("Your account is not verified. Please check your email for OTP or sign up again.")
                if st.button("Resend OTP"):
                    otp = generate_otp()
                    # Store OTP in database with expiry timestamp (10 minutes from now)
                    db.users.update_one(
                        {"email": email},
                        {"$set": {
                            "otp": str(otp),
                            "otp_expiry": time.time() + 600  # 10 minutes
                        }}
                    )
                    if send_otp(email, otp, user["name"]):
                        st.session_state.email_for_verification = email
                        st.session_state.current_page = 'verify_otp'
                        st.success("OTP sent successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to send OTP. Please try again.")
                return
                
            st.session_state.authenticated = True
            st.session_state.user_id = str(user["_id"])
            st.session_state.user_name = user["name"]
            st.session_state.current_page = 'home'
            
            # Update last login timestamp
            db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": db.get_timestamp()}}
            )
            
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid email or password")
    
    # Navigation buttons (in columns for better layout)
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("← Back to Home", key="login_back_home", use_container_width=True):
            st.session_state.current_page = 'landing'
            st.rerun()
    
    with col2:
        if st.button("Sign Up", key="to_signup", use_container_width=True):
            st.session_state.current_page = 'signup'
            st.rerun()
    
    with col3:
        if st.button("✨ Sign in with Google", key="google_signin", use_container_width=True):
            st.session_state.current_page = 'google_auth'
            st.rerun()

def signup_page():
    """Display signup page and handle registration"""
    st.markdown("<h1 class='main-header'>📝 Sign Up</h1>", unsafe_allow_html=True)
    
    # Signup form
    with st.form("signup_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_button = st.form_submit_button("Sign Up")
    
    # Handle form submission
    if submit_button:
        if not name or not email or not password or not confirm_password:
            st.error("Please fill out all fields")
            return
        
        # Validate email format
        if not validate_email(email):
            st.error("Please enter a valid email address")
            return
        
        # Additional email validation
        if not is_valid_email(email):
            st.error("Please enter a valid email address with a common domain")
            return
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            st.error(message)
            return
        
        # Confirm passwords match
        if password != confirm_password:
            st.error("Passwords do not match")
            return
        
        # Check if email already exists
        db = get_db_connection()
        existing_user = db.users.find_one({"email": email})
        
        if existing_user:
            st.error("Email already registered. Please log in or use a different email")
            return
        
        # Hash password for storage
        hashed_password = hash_password(password)
        
        # Generate OTP
        otp = generate_otp()
        
        # Create new user (unverified)
        new_user = {
            "name": name,
            "email": email,
            "password": hashed_password,
            "created_at": db.get_timestamp(),
            "last_login": None,
            "is_verified": False,
            "otp": str(otp),
            "otp_expiry": time.time() + 600  # 10 minutes
        }
        
        result = db.users.insert_one(new_user)
        
        if result.inserted_id:
            # Send OTP via email
            if send_otp(email, otp, name):
                st.session_state.email_for_verification = email
                st.session_state.current_page = 'verify_otp'
                st.success("Account created! Please verify your email with the OTP sent.")
                st.rerun()
            else:
                # If OTP sending fails, still create account but notify user
                st.warning("Account created but failed to send verification OTP. Please contact support.")
        else:
            st.error("Failed to create account. Please try again")
    
    # Navigation buttons (in columns for better layout)
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("← Back to Home", key="signup_back_home", use_container_width=True):
            st.session_state.current_page = 'landing'
            st.rerun()
    
    with col2:
        if st.button("Login", key="to_login", use_container_width=True):
            st.session_state.current_page = 'login'
            st.rerun()
    
    with col3:
        if st.button("✨ Sign up with Google", key="google_signup", use_container_width=True):
            st.session_state.current_page = 'google_auth'
            st.rerun()