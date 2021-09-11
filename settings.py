import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BEATBOT_TOKEN")
OWNER = int(os.getenv("BEATBOT_OWNER"))
PREFIX = os.getenv("BEATBOT_PREFIX")