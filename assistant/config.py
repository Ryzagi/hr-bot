import os
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

ADMIN_TG_ID = os.environ["ADMIN_TG_ID"]
HR_CHAT_ID = os.environ["HR_CHAT_ID"]

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_ROOT_PAGE_ID = os.environ["NOTION_ROOT_PAGE_ID"]