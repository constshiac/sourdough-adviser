import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Supabase — optional locally, required in production
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")
SUPABASE_SERVICE_KEY=os.environ.get("SUPABASE_SERVICE_KEY", "")

# JWT secret for signing tokens
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

# Dev user ID for testing without auth
_DEV_USER_ID = "00000000-0000-0000-0000-000000000001"