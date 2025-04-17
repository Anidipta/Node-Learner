import os
import streamlit as st
import google.generativeai as genai
import groq
import random
import json
import re
from typing import List, Dict, Any

# Initialize AI providers
def initialize_ai_providers():
    # Google AI
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if google_api_key:
        genai.configure(api_key=google_api_key)
    
    # GROQ
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if groq_api_key:
        groq_client = groq.Client(api_key=groq_api_key)
    else:
        groq_client = None
    
    return groq_client

# Singleton pattern for AI client
@st.cache_resource
def get_ai_clients():
    return initialize_ai_providers()

def get_ai_explanation(topic: str, detail_level: str = "Intermediate") -> str:
    """
    Get AI-generated explanation for a topic with specified detail level.
    
    Args:
        topic: The topic to explain
        detail_level: Level of detail (Basic, Intermediate, Advanced, Expert)
    
    Returns:
        A detailed explanation of the topic
    """
    groq_client = get_ai_clients()
    
    # Create prompt based on detail level
    depth_mapping = {
        "Basic": "beginner-friendly, focusing on fundamental concepts with simple examples",
        "Intermediate": "moderately detailed, covering main concepts with some nuance",
        "Advanced": "in-depth, including technical details and sophisticated concepts",
        "Expert": "comprehensive and technically precise, including cutting-edge research and specialized terminology"
    }
    
    complexity = depth_mapping.get(detail_level, depth_mapping["Intermediate"])
    
    prompt = f"""
    Provide a {complexity} explanation of "{topic}".
    
    Include:
    1. Clear definition and key concepts
    2. Important context or background
    3. Practical applications or relevance
    4. Related concepts that would help understanding
    
    Format your response in clear, engaging markdown that's easy to follow.
    Limit your response to 3-5 paragraphs maximum.
    """
    
    # Try GROQ first if available
    if groq_client:
        try:
            response = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",  # Use an appropriate GROQ model
                messages=[
                    {"role": "system", "content": "You are an educational assistant focused on providing clear, accurate, and engaging explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            st.warning(f"Error with GROQ API: {e}. Falling back to Google AI.")
    
    # Fall back to Google Generative AI
    try:
        model = genai.GenerativeModel('gemini-pro')
        result = model.generate_content(prompt)
        return result.text
    except Exception as e:
        # If both APIs fail, return a basic explanation
        st.error(f"AI explanation generation failed: {e}")
        return f"**{topic}**\n\nBasic explanation: This topic relates to {topic.lower()}. For a more detailed understanding, you may want to explore related concepts and resources."

def get_youtube_links(topic: str, count: int = 3) -> List[Dict[str, str]]:
    """
    Generate relevant YouTube links for a given topic.
    
    In a real application, this would use the YouTube API.
    For this demo, we'll generate simulated links.
    
    Args:
        topic: The topic to find videos for
        count: Number of links to generate
        
    Returns:
        List of dicts with title and url
    """
    # In a production app, you would use YouTube API here
    # For this demo, we'll create simulated educational links
    
    # Clean the topic for URL
    clean_topic = re.sub(r'[^\w\s]', '', topic).replace(' ', '+')
    
    # Create fake but plausible YouTube links
    links = []
    titles = [
        f"Understanding {topic}: A Complete Guide",
        f"{topic} Explained Simply",
        f"Deep Dive into {topic}",
        f"{topic} - From Beginner to Expert",
        f"The Science Behind {topic}",
        f"How {topic} Works - Visual Explanation"
    ]
    
    # Shuffle and take requested count
    random.shuffle(titles)
    selected_titles = titles[:count]
    
    for title in selected_titles:
        video_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=11))
        links.append({
            "title": title,
            "url": f"https://www.youtube.com/watch?v={video_id}"
        })
    
    return links

def get_related_concepts(topic: str, count: int = 5) -> List[str]:
    """
    Generate related concepts/topics for a given topic.
    
    Args:
        topic: The main topic
        count: Number of related concepts to generate
        
    Returns:
        List of related concept strings
    """
    groq_client = get_ai_clients()
    
    prompt = f"""
    Generate {count} related concepts or subtopics for "{topic}". 
    Return only a JSON array of strings, with no additional text or explanation.
    Example output format: ["Related Topic 1", "Related Topic 2", "Related Topic 3"]
    """
    
    # Try GROQ first if available
    if groq_client:
        try:
            response = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": "You are an assistant that returns only valid JSON arrays of related concepts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=512
            )
            try:
                # Try to parse the response as JSON
                content = response.choices[0].message.content
                # Find JSON array in the response
                match = re.search(r'\[.*\]', content, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
                else:
                    # If no JSON array pattern, try parsing the whole response
                    return json.loads(content)
            except json.JSONDecodeError:
                # If parsing fails, extract strings manually
                content = response.choices[0].message.content
                # Extract anything that looks like list items
                items = re.findall(r'"([^"]+)"', content)
                return items[:count]
        except Exception as e:
            st.warning(f"Error with GROQ API for related concepts: {e}. Falling back to Google AI.")
    
    # Fall back to Google Generative AI
    try:
        model = genai.GenerativeModel('gemini-pro')
        result = model.generate_content(prompt)
        try:
            # Try to parse the response as JSON
            return json.loads(result.text)
        except json.JSONDecodeError:
            # If parsing fails, extract strings manually
            items = re.findall(r'"([^"]+)"', result.text)
            return items[:count]
    except Exception as e:
        # If both APIs fail, return generic related concepts
        st.error(f"Related concepts generation failed: {e}")
        return [f"{topic} basics", f"{topic} applications", f"{topic} examples", f"{topic} history", f"{topic} future"]

class AIExplainer:
    """Class to handle AI explanations with caching and context management"""
    
    def __init__(self):
        self.explanations_cache = {}
        
    def get_explanation(self, topic: str, detail_level: str = "Intermediate") -> Dict[str, Any]:
        """Get a complete explanation package for a topic"""
        cache_key = f"{topic}_{detail_level}"
        
        # Return cached explanation if available
        if cache_key in self.explanations_cache:
            return self.explanations_cache[cache_key]
        
        # Generate new explanation
        explanation = get_ai_explanation(topic, detail_level)
        links = get_youtube_links(topic)
        related = get_related_concepts(topic)
        
        result = {
            "explanation": explanation,
            "links": links,
            "related_topics": related,
            "detail_level": detail_level
        }
        
        # Cache the result
        self.explanations_cache[cache_key] = result
        return result
        
    def clear_cache(self):
        """Clear the explanations cache"""
        self.explanations_cache = {}

# Create a singleton instance
@st.cache_resource
def get_explainer():
    return AIExplainer()