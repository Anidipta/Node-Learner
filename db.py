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

    def save_knowledge_tree(self, user_id, topic, nodes_dict, edges_dict, graph_image=None, update=False):
        """
        Save a knowledge tree to the database
        
        Args:
            user_id (ObjectId): User ID
            topic (str): Main topic of the tree
            nodes_dict (dict): Dictionary of nodes
            edges_dict (dict): Dictionary of edges
            graph_image (bytes, optional): PNG image data of the graph
            update (bool, optional): Whether to update an existing tree
            
        Returns:
            ObjectId: Tree ID
        """
        try:
            # Store the image in GridFS if provided
            image_id = None
            if graph_image:
                image_id = self.fs.put(
                    graph_image,
                    filename=f"{topic}_graph.png",
                    content_type="image/png"
                )
            
            # Combine data
            graph_data = {
                "nodes": nodes_dict,
                "edges": edges_dict
            }
            
            # Create tree document
            tree = {
                "user_id": user_id,
                "topic": topic,
                "created_at": datetime.datetime.now(),
                "graph_data": graph_data,
                "image_id": image_id
            }
            
            if update:
                # Update existing tree
                result = self.db.knowledge_trees.update_one(
                    {"user_id": user_id, "topic": topic},
                    {"$set": tree},
                    upsert=True
                )
                return topic  # Return topic as ID for update
            else:
                # Insert new tree
                result = self.db.knowledge_trees.insert_one(tree)
                return result.inserted_id
                
        except Exception as e:
            st.error(f"Error saving knowledge tree: {e}")
            return None
    
    def save_learning_session(self, user_id, topic, tree_id, time_spent, nodes_explored):
            """
            Save a learning session to the database
            
            Args:
                user_id (ObjectId): User ID
                topic (str): Topic explored
                tree_id (ObjectId): ID of the knowledge tree
                time_spent (int): Time spent in seconds
                nodes_explored (list): List of explored node IDs
                
            Returns:
                ObjectId: Session ID
            """
            try:
                session = {
                    "user_id": user_id,
                    "topic": topic,
                    "tree_id": tree_id,
                    "timestamp": datetime.datetime.now(),
                    "time_spent": time_spent,
                    "nodes_explored": nodes_explored
                }
                
                result = self.learning_sessions.insert_one(session)
                return result.inserted_id
                
            except Exception as e:
                st.error(f"Error saving learning session: {e}")
                return None
        
    def get_learning_stats(self, user_id):
            """
            Get learning statistics for a user
            
            Args:
                user_id (ObjectId): User ID
                
            Returns:
                dict: Learning statistics
            """
            try:
                # Total sessions
                total_sessions = self.learning_sessions.count_documents({"user_id": user_id})
                
                # Topics explored
                distinct_topics = len(self.learning_sessions.distinct("topic", {"user_id": user_id}))
                
                # Total time spent
                pipeline = [
                    {"$match": {"user_id": user_id}},
                    {"$group": {"_id": None, "total_time": {"$sum": "$time_spent"}}}
                ]
                result = list(self.learning_sessions.aggregate(pipeline))
                total_time = result[0]["total_time"] if result else 0
                
                # Learning streak calculation
                now = datetime.datetime.now()
                streak_days = 0
                current_date = now.date()
                
                # Check last 30 days for continuous learning
                for i in range(30):
                    day = current_date - datetime.timedelta(days=i)
                    day_start = datetime.datetime.combine(day, datetime.time.min)
                    day_end = datetime.datetime.combine(day, datetime.time.max)
                    
                    sessions_count = self.learning_sessions.count_documents({
                        "user_id": user_id,
                        "timestamp": {"$gte": day_start, "$lte": day_end}
                    })
                    
                    if sessions_count > 0:
                        streak_days += 1
                    else:
                        # Break streak if a day is missed
                        break
                
                return {
                    "total_sessions": total_sessions,
                    "topics_explored": distinct_topics,
                    "total_time": total_time,
                    "learning_streak": streak_days
                }
                
            except Exception as e:
                st.error(f"Error calculating learning stats: {e}")
                return {
                    "total_sessions": 0,
                    "topics_explored": 0,
                    "total_time": 0,
                    "learning_streak": 0
                }
        
    def search_learning_history(self, user_id, query):
            """
            Search learning history for a user
            
            Args:
                user_id (ObjectId): User ID
                query (str): Search query
                
            Returns:
                list: Matching learning sessions
            """
            try:
                # Search by topic
                results = list(self.learning_sessions.find({
                    "user_id": user_id,
                    "topic": {"$regex": query, "$options": "i"}
                }).sort("timestamp", -1))
                
                # Search by nodes explored
                node_results = list(self.learning_sessions.find({
                    "user_id": user_id,
                    "nodes_explored": {"$regex": query, "$options": "i"}
                }).sort("timestamp", -1))
                
                # Combine and remove duplicates
                all_results = results + [r for r in node_results if r["_id"] not in [res["_id"] for res in results]]
                
                return all_results
                
            except Exception as e:
                st.error(f"Error searching learning history: {e}")
                return []
        
    def get_knowledge_tree(self, tree_id):
            """
            Get a knowledge tree from the database
            
            Args:
                tree_id (ObjectId): Tree ID
                
            Returns:
                dict: Knowledge tree data
            """
            try:
                tree = self.db.knowledge_trees.find_one({"_id": ObjectId(tree_id)})
                return tree
                
            except Exception as e:
                st.error(f"Error retrieving knowledge tree: {e}")
                return None
        
    def get_graph_image(self, image_id):
            """
            Get a graph image from GridFS
            
            Args:
                image_id (ObjectId): Image ID
                
            Returns:
                bytes: Image data
            """
            try:
                if image_id:
                    image = self.fs.get(ObjectId(image_id))
                    return image.read()
                return None
                
            except Exception as e:
                st.error(f"Error retrieving graph image: {e}")
                return None

# Connection singleton
_db_connection = None

def get_db_connection():
        """Get or create MongoDB connection"""
        global _db_connection
        
        if _db_connection is None:
            _db_connection = MongoDBConnection()
            _db_connection.connect()
        
        return _db_connection