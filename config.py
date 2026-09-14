import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def get_config(key, default=""):
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)

# ---------------- LLM ----------------
GROQ_API_KEY = get_config("GROQ_API_KEY")
GROQ_MODEL = get_config("GROQ_MODEL", "llama-3.3-70b-versatile")

# ---------------- Web search ----------------
TAVILY_API_KEY = get_config("TAVILY_API_KEY")

# ---------------- Admin auth ----------------
ADMIN_USERNAME = get_config("ADMIN_USERNAME")
ADMIN_PASSWORD = get_config("ADMIN_PASSWORD")

# ---------------- SMTP ----------------
SMTP_HOST = get_config("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(get_config("SMTP_PORT", "587"))
SMTP_USER = get_config("SMTP_USER")
SMTP_PASSWORD = get_config("SMTP_PASSWORD")

# ---------------- Organization profile ----------------
ORG_PROFILE = {
    "name": get_config("ORG_NAME", "Your Organization"),
    "website": get_config("ORG_WEBSITE"),
    "services": get_config("ORG_SERVICES"),
    "description": get_config("ORG_DESCRIPTION"),
    "sender_name": get_config("ORG_SENDER_NAME", "Admin"),
    "sender_title": get_config("ORG_SENDER_TITLE", "Business Development"),
}

MAX_REVIEW_ITERATIONS = 3