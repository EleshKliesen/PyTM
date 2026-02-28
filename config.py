import os

from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

PROJECT_NAME = os.getenv("PROJECT_NAME")
VERSION = os.getenv("VERSION")

CLUB_ID = os.getenv("CLUB_ID")

USER_AGENT = f"{PROJECT_NAME}/{VERSION} ({EMAIL})"
