import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    print("CRITICAL: MONGODB_URI is not set in backend/.env")
    raise ValueError("MONGODB_URI is not set in backend/.env")

client = MongoClient(MONGODB_URI)
db = client.resume_analyzer


def get_db():
    return db
