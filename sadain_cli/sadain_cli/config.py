import os
from dotenv import load_dotenv

load_dotenv()

def load_api_key():
    """Loads the API key from the environment."""
    return os.getenv("GROQ_API_KEY")
