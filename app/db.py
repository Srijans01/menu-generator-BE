from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fetch the MongoDB connection URI and database name from environment variables
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

# Check if the environment variables are loaded correctly
if not MONGO_URI or not MONGO_DB_NAME:
    raise ValueError("MONGO_URI and MONGO_DB_NAME must be set")

# Create the MongoDB client and database connection
client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Optional: Access specific collections directly
restaurants_collection = db["restaurants"]

# Print the connection string (for debugging)
print(f"Connected to MongoDB at: {MONGO_URI}")
print(f"Using database: {MONGO_DB_NAME}")
