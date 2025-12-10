import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get MongoDB configuration from environment
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "recipe_crawler")

# Create MongoDB client
client = MongoClient(MONGO_URI)

# Get database
db = client[MONGO_DB_NAME]

# Export commonly used collections
meals_collection = db.meals

# Test connection
def test_connection():
    """Test MongoDB connection"""
    try:
        client.admin.command('ping')
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False