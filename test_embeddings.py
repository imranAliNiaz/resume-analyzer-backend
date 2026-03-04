from langchain_google_genai import GoogleGenerativeAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

models = [
    "embedding-001",
    "text-embedding-004",
    "models/embedding-001",
    "models/text-embedding-004",
]

for model in models:
    print(f"Testing model: {model}")
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model=model, google_api_key=api_key)
        embeddings.embed_query("test")
        print(f"SUCCESS with {model}")
        break
    except Exception as e:
        print(f"FAILED with {model}: {e}")
