import os
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# MongoDB connection class
class MongoDBConnection:
    def __init__(self):
        """Initialize MongoDB connection with environment variables"""
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.db_name = os.getenv("DB_NAME", "nodelearn")
        self.client = None
        self.db = None
        self.users = None
        self.knowledge_trees = None
        self.learning_sessions = None
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            
            # Initialize collections
            self.users = self.db.users
            self.knowledge_trees = self.db.knowledge_trees
            self.learning_sessions = self.db.learning_sessions
            
            # Create indexes for better performance
            self.users.create_index("email", unique=True)
            self.knowledge_trees.create_index([("user_id", 1), ("topic", 1)])
            self.learning_sessions.create_index("user_id")
            
            return True
        except Exception as e:
            st.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
    
    def get_timestamp(self):
        """Get current timestamp for database records"""
        return datetime.datetime.utcnow()

    def save_knowledge_tree(self, user_id, topic, nodes, edges):
        """Save knowledge tree to database"""
        tree_data = {
            "user_id": user_id,
            "topic": topic,
            "nodes": nodes,
            "edges": edges,
            "created_at": self.get_timestamp(),
            "updated_at": self.get_timestamp()
        }
        
        # Check if tree already exists for this user and topic
        existing_tree = self.knowledge_trees.find_one({
            "user_id": user_id,
            "topic": topic
        })
        
        if existing_tree:
            # Update existing tree
            self.knowledge_trees.update_one(
                {"_id": existing_tree["_id"]},
                {
                    "$set": {
                        "nodes": nodes,
                        "edges": edges,
                        "updated_at": self.get_timestamp()
                    }
                }
            )
            return str(existing_tree["_id"])
        else:
            # Insert new tree
            result = self.knowledge_trees.insert_one(tree_data)
            return str(result.inserted_id)
    
    def get_knowledge_tree(self, user_id, topic=None, tree_id=None):
        """Get knowledge tree by user_id and topic or tree_id"""
        if tree_id:
            from bson.objectid import ObjectId
            return self.knowledge_trees.find_one({"_id": ObjectId(tree_id)})
        elif topic:
            return self.knowledge_trees.find_one({
                "user_id": user_id,
                "topic": topic
            })
        else:
            # Return all trees for this user
            return list(self.knowledge_trees.find({"user_id": user_id}))
    
    def log_learning_session(self, user_id, topic, tree_id, nodes_explored, time_spent):
        """Log a learning session for analytics"""
        session_data = {
            "user_id": user_id,
            "topic": topic,
            "tree_id": tree_id,
            "nodes_explored": nodes_explored,
            "time_spent": time_spent,  # in seconds
            "timestamp": self.get_timestamp()
        }
        
        self.learning_sessions.insert_one(session_data)
    
    def get_learning_history(self, user_id, limit=10):
        """Get user's learning history"""
        return list(self.learning_sessions.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit))
    
    def search_topics(self, user_id, query):
        """Search for topics in user's knowledge trees"""
        return list(self.knowledge_trees.find({
            "user_id": user_id,
            "topic": {"$regex": query, "$options": "i"}
        }))

# Connection singleton
_db_connection = None

def get_db_connection():
    """Get or create MongoDB connection"""
    global _db_connection
    
    if _db_connection is None:
        _db_connection = MongoDBConnection()
        _db_connection.connect()
    
    return _db_connection
