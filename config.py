import os
from dotenv import load_dotenv

load_dotenv()

config = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "base_url": os.getenv("OPENAI_BASE_URL"),
}
