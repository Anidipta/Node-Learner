import os
import json
import time
import requests
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

class AIExplorer:
    """Interface with AI models for knowledge exploration"""
    
    def __init__(self, provider="google"):
        """Initialize AI provider - google or groq"""
        self.provider = provider.lower()
        
        # Set API keys from environment variables
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyBSPA2m6-UakS7cWWiJ79AsGrC1Murm4UA")
        self.groq_api_key = os.getenv("GROQ_API_KEY", "")
        
        # Check if API keys are available
        if self.provider == "google" and not self.google_api_key:
            st.warning("Google Generative AI API key not found. Some features may not work.")
        
        if self.provider == "groq" and not self.groq_api_key:
            st.warning("GROQ API key not found. Some features may not work.")
    
    def explore_topic(self, topic, depth=1):
        """
        Explore a topic using AI and return related concepts
        
        Args:
            topic (str): The main topic to explore
            depth (int): The depth of exploration (1-3)
            
        Returns:
            dict: Topic information and related concepts
        """
        if self.provider == "google":
            return self._explore_with_google(topic, depth)
        elif self.provider == "groq":
            return self._explore_with_groq(topic, depth)
        else:
            st.error(f"Unknown AI provider: {self.provider}")
            return {"error": f"Unknown AI provider: {self.provider}"}
    
    def _explore_with_google(self, topic, depth=1):
        """Use Google Generative AI to explore a topic"""
        try:
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.google_api_key
            }
            
            # Create prompt based on depth
            if depth == 1:
                prompt = f"""
                Create a precise to the point structured exploration of the topic "{topic}". No Historial Contexts.
                Return a JSON object with the following structure:
                {{
                    "topic": "{topic}",
                    "summary": "A 2-3 sentence summary of the topic",
                    "related_concepts": [
                        {{
                            "name": "Related concept 1",
                            "relation": "How it relates to the main topic",
                            "summary": "Brief 1-sentence explanation"
                        }},
                        ...up to 3 related concepts...
                    ]
                }}
                Only return the JSON data with no additional text or explanation.
                """
            else:
                prompt = f"""
                Create a detailed exploration of the topic "{topic}".No Historial Contexts.
                Return a JSON object with the following structure:
                {{
                    "topic": "{topic}",
                    "summary": "A 4-5 sentence detailed explanation of the topic",
                    "key_points": ["Point 1", "Point 2", "Point 3"],
                    "related_concepts": [
                        {{
                            "name": "Related concept 1",
                            "relation": "How it relates to the main topic",
                            "summary": "2-3 sentence explanation"
                        }},
                        ...up to 7 related concepts...
                    ],
                    "subtopics": [
                        {{
                            "name": "Subtopic 1",
                            "summary": "Brief explanation"
                        }},
                        ...up to 5 subtopics...
                    ]
                }}
                Only return the JSON data with no additional text or explanation.
                """
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            text_result = result['candidates'][0]['content']['parts'][0]['text']
            
            # Extract JSON from response (in case there's additional text)
            json_str = text_result.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:]
            if json_str.endswith('```'):
                json_str = json_str[:-3]
                
            return json.loads(json_str)
        
        except Exception as e:
            st.error(f"Error with Google AI: {e}")
            return {
                "topic": topic,
                "summary": f"Failed to explore topic: {str(e)}",
                "related_concepts": []
            }
    
    def _explore_with_groq(self, topic, depth=1):
        """Use GROQ to explore a topic"""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.groq_api_key}"
            }
            
            # Create prompt based on depth
            if depth == 1:
                prompt = f"""
                Create a structured exploration of the topic "{topic}". No Historial Contexts.
                Return a JSON object with the following structure:
                {{
                    "topic": "{topic}",
                    "summary": "A 2-3 sentence summary of the topic",
                    "related_concepts": [
                        {{
                            "name": "Related concept 1",
                            "relation": "How it relates to the main topic",
                            "summary": "Brief 1-sentence explanation"
                        }},
                        ...up to 5 related concepts...
                    ]
                }}
                Only return the JSON data with no additional text or explanation.
                """
            else:
                prompt = f"""
                Create a detailed exploration of the topic "{topic}".No Historial Contexts.
                Return a JSON object with the following structure:
                {{
                    "topic": "{topic}",
                    "summary": "A 4-5 sentence detailed explanation of the topic",
                    "key_points": ["Point 1", "Point 2", "Point 3"],
                    "related_concepts": [
                        {{
                            "name": "Related concept 1",
                            "relation": "How it relates to the main topic",
                            "summary": "2-3 sentence explanation"
                        }},
                        ...up to 7 related concepts...
                    ],
                    "subtopics": [
                        {{
                            "name": "Subtopic 1",
                            "summary": "Brief explanation"
                        }},
                        ...up to 5 subtopics...
                    ]
                }}
                Only return the JSON data with no additional text or explanation.
                """
            
            data = {
                "model": "llama3-70b-8192",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that provides well-structured JSON responses for knowledge exploration."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            text_result = result['choices'][0]['message']['content']
            
            # Extract JSON from response (in case there's additional text)
            json_str = text_result.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:]
            if json_str.endswith('```'):
                json_str = json_str[:-3]
                
            return json.loads(json_str)
        
        except Exception as e:
            st.error(f"Error with GROQ AI: {e}")
            return {
                "topic": topic,
                "summary": f"Failed to explore topic: {str(e)}",
                "related_concepts": []
            }
    
    def get_detailed_explanation(self, topic):
        """Get a detailed explanation of a specific topic"""
        try:
            if self.provider == "google":
                url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.google_api_key
                }
                
                prompt = f"""
                Provide a detailed explanation of the topic "{topic}".
                Include:
                - A clear definition or introduction
                - Key concepts and principles
                - Important applications or examples
                - Historical context if relevant
                
                Format your response in markdown for readability.
                """
                
                data = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }]
                }
                
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                
                result = response.json()
                explanation = result['candidates'][0]['content']['parts'][0]['text']
                
            elif self.provider == "groq":
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.groq_api_key}"
                }
                
                prompt = f"""
                Provide a detailed explanation of the topic "{topic}".
                Include:
                - A clear definition or introduction
                - Key concepts and principles
                - Important applications or examples
                - Historical context if relevant
                
                Format your response in markdown for readability.
                """
                
                data = {
                    "model": "llama3-70b-8192",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that provides clear educational content."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                }
                
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                
                result = response.json()
                explanation = result['choices'][0]['message']['content']
            
            return explanation
        
        except Exception as e:
            st.error(f"Error getting explanation: {e}")
            return f"Failed to get explanation for {topic}: {str(e)}"
            
    def explore_subtopic(self, main_topic, subtopic):
        """
        Explore a specific subtopic of a main topic
        
        Args:
            main_topic (str): The main topic
            subtopic (str): The subtopic to explore
            
        Returns:
            dict: Subtopic information and related concepts
        """
        try:
            if self.provider == "google":
                url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.google_api_key
                }
                
                prompt = f"""
                Create a detailed exploration of the subtopic "{subtopic}" related to "{main_topic}".
                Return a JSON object with the following structure:
                {{
                    "subtopic": "{subtopic}",
                    "main_topic": "{main_topic}",
                    "summary": "A 3-4 sentence detailed explanation of how this subtopic relates to the main topic",
                    "key_points": ["Point 1", "Point 2", "Point 3"],
                    "related_concepts": [
                        {{
                            "name": "Related concept 1",
                            "relation": "How it relates to this subtopic",
                            "summary": "Brief explanation"
                        }},
                        ...up to 4 related concepts...
                    ]
                }}
                Only return the JSON data with no additional text or explanation.
                """
                
                data = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }]
                }
                
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                
                result = response.json()
                text_result = result['candidates'][0]['content']['parts'][0]['text']
                
                # Extract JSON from response
                json_str = text_result.strip()
                if json_str.startswith('```json'):
                    json_str = json_str[7:]
                if json_str.endswith('```'):
                    json_str = json_str[:-3]
                    
                return json.loads(json_str)
            
            elif self.provider == "groq":
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.groq_api_key}"
                }
                
                prompt = f"""
                Create a detailed exploration of the subtopic "{subtopic}" related to "{main_topic}".
                Return a JSON object with the following structure:
                {{
                    "subtopic": "{subtopic}",
                    "main_topic": "{main_topic}",
                    "summary": "A 3-4 sentence detailed explanation of how this subtopic relates to the main topic",
                    "key_points": ["Point 1", "Point 2", "Point 3"],
                    "related_concepts": [
                        {{
                            "name": "Related concept 1",
                            "relation": "How it relates to this subtopic",
                            "summary": "Brief explanation"
                        }},
                        ...up to 4 related concepts...
                    ]
                }}
                Only return the JSON data with no additional text or explanation.
                """
                
                data = {
                    "model": "llama3-70b-8192",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that provides well-structured JSON responses for knowledge exploration."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                }
                
                response = requests.post(url, headers=headers, json=data)
                response.raise_for_status()
                
                result = response.json()
                text_result = result['choices'][0]['message']['content']
                
                # Extract JSON from response
                json_str = text_result.strip()
                if json_str.startswith('```json'):
                    json_str = json_str[7:]
                if json_str.endswith('```'):
                    json_str = json_str[:-3]
                    
                return json.loads(json_str)
                
        except Exception as e:
            st.error(f"Error exploring subtopic: {e}")
            return {
                "subtopic": subtopic,
                "main_topic": main_topic,
                "summary": f"Failed to explore subtopic: {str(e)}",
                "related_concepts": []
            }