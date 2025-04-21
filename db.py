import os
import datetime
from typing import Dict, Any, List, Optional
from bson.objectid import ObjectId
from pymongo import MongoClient, TEXT, DESCENDING
from pymongo.collection import Collection
from bson.binary import Binary
from gridfs import GridFS
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# MongoDB Connection Singleton
_db_connection = None

class MongoDBConnection:
    def __init__(self):
        """Initialize MongoDB connection using environment variables"""
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.db_name = os.getenv("DB_NAME", "nodelearn")
        self.client: Optional[MongoClient] = None
        self.db: Optional[Any] = None
        self.fs: Optional[GridFS] = None

        # Collections
        self.users: Optional[Collection] = None
        self.knowledge_trees: Optional[Collection] = None
        self.learning_sessions: Optional[Collection] = None

    def connect(self) -> bool:
        """Establish a connection to MongoDB and initialize collections and indexes"""
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.db_name]
            self.fs = GridFS(self.db)

            # Initialize collections
            self.users = self.db.users
            self.knowledge_trees = self.db.knowledge_trees
            self.learning_sessions = self.db.learning_sessions

            # Create indexes
            self.users.create_index("email", unique=True)
            self.knowledge_trees.create_index([("user_id", 1), ("topic", 1)])
            self.learning_sessions.create_index("user_id")
            self.learning_sessions.create_index([("nodes", TEXT)])
            self.learning_sessions.create_index([("created_at", DESCENDING)])

            return True
        except Exception as e:
            st.error(f"Failed to connect to MongoDB: {e}")
            return False
    
    def get_all_sessions(self):
        try:
            return list(self.learning_sessions.find())
        except Exception as e:
            st.error(f"Error fetching sessions: {e}")
            return []

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()

    def get_timestamp(self):
        """Return the current UTC timestamp"""
        return datetime.datetime.utcnow()

    def save_knowledge_tree(self, user_id, topic, nodes_dict, edges_dict, graph_image=None, update=False):
        """Save or update a knowledge tree"""
        try:
            image_id = None
            if graph_image:
                image_id = self.fs.put(graph_image, filename=f"{topic}_graph.png", content_type="image/png")

            tree_doc = {
                "user_id": user_id,
                "topic": topic,
                "created_at": datetime.datetime.utcnow(),
                "graph_data": {
                    "nodes": nodes_dict,
                    "edges": edges_dict
                },
                "image_id": image_id
            }

            if update:
                self.knowledge_trees.update_one(
                    {"user_id": user_id, "topic": topic},
                    {"$set": tree_doc},
                    upsert=True
                )
                return topic
            else:
                result = self.knowledge_trees.insert_one(tree_doc)
                return result.inserted_id

        except Exception as e:
            st.error(f"Error saving knowledge tree: {e}")
            return None

    def get_knowledge_tree(self, user_id, topic=None):
        """
        Retrieve knowledge trees for a user from the database.
        
        Parameters:
        - user_id (str): The ID of the user whose knowledge trees to retrieve
        - topic (str, optional): If provided, filters results to trees with this specific topic
        
        Returns:
        - list: A list of knowledge tree documents, each containing topic, nodes, edges, and metadata
        """
        try:
            # Connect to knowledge_trees collection
            collection = self.db.knowledge_trees
            
            # Build query - always filter by user_id
            query = {"user_id": user_id}
            
            # Add topic filter if provided
            if topic:
                query["topic"] = topic
                
            # Execute query and return results as a list
            # Sort by last_modified date to show most recent first
            cursor = collection.find(query).sort("last_modified", -1)
            return list(cursor)
        except Exception as e:
            print(f"Error retrieving knowledge tree: {e}")
            return []
        
    def get_knowledge_tree_by_id(self, tree_id):
        """
        Retrieve a specific knowledge tree from the database using its ID.
        
        Parameters:
        - tree_id (str): The unique identifier of the knowledge tree to retrieve
        
        Returns:
        - dict: The knowledge tree document or None if not found
        """
        try:
            # Connect to knowledge_trees collection
            collection = self.db.knowledge_trees
            
            # Convert string ID to ObjectId if necessary
            from bson.objectid import ObjectId
            if isinstance(tree_id, str):
                tree_id = ObjectId(tree_id)
                
            # Find the document with the matching ID
            tree_doc = collection.find_one({"_id": tree_id})
            
            return tree_doc
        except Exception as e:
            print(f"Error retrieving knowledge tree by ID: {e}")
            return None
    
    def log_learning_session(self, user_id, topic, tree_id, nodes_explored, time_spent):
        """
        Log a user's learning session for analytics and history tracking.
        
        Parameters:
        - user_id (str): The ID of the user who explored the knowledge tree
        - topic (str): The main topic of the knowledge tree
        - tree_id (str): The unique identifier of the knowledge tree
        - nodes_explored (list): List of node names that were explored during the session
        - time_spent (int): Time spent exploring the tree in seconds
        
        Returns:
        - str: ID of the logged session document or None if logging failed
        """
        try:
            # Connect to learning_sessions collection
            collection = self.db.learning_sessions
            
            # Create session document
            session_doc = {
                "user_id": user_id,
                "topic": topic,
                "tree_id": tree_id,
                "nodes_explored": nodes_explored,
                "node_count": len(nodes_explored),
                "time_spent": time_spent,
                "timestamp": datetime.datetime.now(),
                "session_date": datetime.datetime.now().strftime("%Y-%m-%d")
            }
            
            # Insert session document
            result = collection.insert_one(session_doc)
            
            # Update user statistics
            self._update_user_learning_stats(user_id, time_spent, len(nodes_explored))
            
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error logging learning session: {e}")
            return None
            
    def _update_user_learning_stats(self, user_id, time_spent, nodes_count):
        """
        Update user's learning statistics after a session.
        
        Parameters:
        - user_id (str): The ID of the user
        - time_spent (int): Time spent exploring in seconds
        - nodes_count (int): Number of nodes explored in this session
        """
        try:
            # Connect to users collection
            collection = self.db.users
            
            # Update user document with incremented stats
            collection.update_one(
                {"_id": user_id},
                {
                    "$inc": {
                        "total_learning_time": time_spent,
                        "total_nodes_explored": nodes_count,
                        "session_count": 1
                    },
                    "$set": {
                        "last_active": datetime.datetime.now()
                    }
                },
                upsert=False
            )
        except Exception as e:
            print(f"Error updating user learning stats: {e}")
        
    def get_graph_image(self, image_id):
        """Retrieve a graph image from GridFS"""
        try:
            if image_id:
                image = self.fs.get(ObjectId(image_id))
                return image.read()
            return None
        except Exception as e:
            st.error(f"Error retrieving graph image: {e}")
            return None

    def save_learning_session(self, user_id, topic, tree_id, time_spent, nodes_explored):
        """Save a learning session"""
        try:
            session = {
                "user_id": user_id,
                "topic": topic,
                "tree_id": tree_id,
                "timestamp": self.get_timestamp(),
                "time_spent": time_spent,
                "nodes_explored": nodes_explored
            }
            result = self.learning_sessions.insert_one(session)
            return result.inserted_id
        except Exception as e:
            st.error(f"Error saving learning session: {e}")
            return None

    def get_learning_history(self, user_id, limit=10):
        """Retrieve recent learning sessions"""
        try:
            return list(self.learning_sessions.find({"user_id": user_id}).sort("timestamp", -1).limit(limit))
        except Exception as e:
            st.error(f"Error retrieving learning history: {e}")
            return []

    def search_topics(self, user_id, query):
        """Search topics in knowledge trees"""
        return list(self.knowledge_trees.find({
            "user_id": user_id,
            "topic": {"$regex": query, "$options": "i"}
        }))

    def search_learning_history(self, user_id, query):
        """Search past sessions by topic or nodes"""
        try:
            topic_results = list(self.learning_sessions.find({
                "user_id": user_id,
                "topic": {"$regex": query, "$options": "i"}
            }).sort("timestamp", -1))

            node_results = list(self.learning_sessions.find({
                "user_id": user_id,
                "nodes_explored": {"$regex": query, "$options": "i"}
            }).sort("timestamp", -1))

            combined_ids = {r["_id"] for r in topic_results}
            unique_node_results = [r for r in node_results if r["_id"] not in combined_ids]
            return topic_results + unique_node_results

        except Exception as e:
            st.error(f"Error searching history: {e}")
            return []

    def get_learning_stats(self, user_id):
        """Aggregate learning stats"""
        try:
            total_sessions = self.learning_sessions.count_documents({"user_id": user_id})
            distinct_topics = len(self.learning_sessions.distinct("topic", {"user_id": user_id}))

            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": None, "total_time": {"$sum": "$time_spent"}}}
            ]
            result = list(self.learning_sessions.aggregate(pipeline))
            total_time = result[0]["total_time"] if result else 0

            now = datetime.datetime.utcnow()
            streak = 0
            for i in range(30):
                day = now.date() - datetime.timedelta(days=i)
                start = datetime.datetime.combine(day, datetime.time.min)
                end = datetime.datetime.combine(day, datetime.time.max)
                if self.learning_sessions.count_documents({"user_id": user_id, "timestamp": {"$gte": start, "$lte": end}}) > 0:
                    streak += 1
                else:
                    break

            return {
                "total_sessions": total_sessions,
                "topics_explored": distinct_topics,
                "total_time": total_time,
                "learning_streak": streak
            }

        except Exception as e:
            st.error(f"Error calculating stats: {e}")
            return {
                "total_sessions": 0,
                "topics_explored": 0,
                "total_time": 0,
                "learning_streak": 0
            }

# Dummy fallback for testing
class DummyCollection:
    def __init__(self):
        self.data = []
        self.counter = 1

    def insert_one(self, document):
        document["_id"] = str(self.counter)
        self.counter += 1
        self.data.append(document)
        return DummyResult(document["_id"])

    def find(self, query=None):
        if not query:
            return self.data
        return [doc for doc in self.data if all(doc.get(k) == v for k, v in query.items())]

    def find_one(self, query):
        return next((doc for doc in self.data if all(doc.get(k) == v for k, v in query.items())), None)

    def count_documents(self, query):
        return len(self.find(query))

    def distinct(self, field, query):
        return list({doc.get(field) for doc in self.find(query)})

    def aggregate(self, pipeline):
        return []

class DummyResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id

# Singleton pattern to reuse the MongoDB connection
def get_db_connection():
    global _db_connection
    if _db_connection is None:
        _db_connection = MongoDBConnection()
        _db_connection.connect()
    return _db_connection

# Example usage
def store_session(session_data: Dict[str, Any]) -> str:
    db = get_db_connection()
    return db.save_learning_session(
        user_id=session_data["_id"],
        topic=session_data["topic"],
        tree_id=session_data["tree_id"],
        time_spent=session_data["time_spent"],
        nodes_explored=session_data["nodes_explored"]
    )
def get_session_by_id(self, session_id):
    try:
        return self.learning_sessions.find_one({"_id": ObjectId(session_id)})
    except Exception as e:
        st.error(f"Error retrieving session by ID: {e}")
        return None

def get_all_sessions():
    db = get_db_connection()
    return db.get_all_sessions()

def search_sessions(query):
    """Search for learning sessions based on a search query"""
    db = get_db_connection()
    try:
        # Search in both topic and nodes_explored fields
        return list(db.learning_sessions.find({
            "$or": [
                {"topic": {"$regex": query, "$options": "i"}},
                {"nodes_explored": {"$regex": query, "$options": "i"}}
            ]
        }).sort("timestamp", -1))
    except Exception as e:
        st.error(f"Error searching sessions: {e}")
        return []

def get_session_by_id(session_id):
    """Retrieve a specific learning session by ID"""
    db = get_db_connection()
    try:
        return db.learning_sessions.find_one({"_id": ObjectId(session_id)})
    except Exception as e:
        st.error(f"Error retrieving session by ID: {e}")
        return None