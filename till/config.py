"""Configuration for the Invoice Reconciliation Agent.

All LLM calls go through LiteLLM, so you can swap models by changing these settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM Models (via LiteLLM) ---
# Format: "provider/model" — see https://docs.litellm.ai/docs/providers

# Used for: extracting structured data from invoice PDFs (vision)
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "gemini/gemini-2.0-flash")

# Used for: generating Gmail search queries from transaction data
SEARCH_QUERY_MODEL = os.getenv("SEARCH_QUERY_MODEL", "gemini/gemini-2.0-flash")

# --- API Keys ---
# LiteLLM picks these up automatically based on the provider prefix
# GEMINI_API_KEY for gemini/* models
# ANTHROPIC_API_KEY for anthropic/* models
# OPENAI_API_KEY for openai/* models

# --- Gmail ---
GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
GMAIL_TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token.json")

# --- Langfuse ---
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
LANGFUSE_ENABLED = bool(LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)

# --- Matching Engine ---
CONFIDENCE_THRESHOLD_AUTO = float(os.getenv("CONFIDENCE_THRESHOLD_AUTO", "0.85"))
CONFIDENCE_THRESHOLD_REVIEW = float(os.getenv("CONFIDENCE_THRESHOLD_REVIEW", "0.50"))
DATE_WINDOW_DAYS = int(os.getenv("DATE_WINDOW_DAYS", "30"))

# --- Server ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))
