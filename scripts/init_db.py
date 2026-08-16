"""
init_db.py — Create all database tables.

Usage:
    python scripts/init_db.py
"""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../room2_backend'))

from dotenv import load_dotenv
load_dotenv()

from database.db import init_db, engine
from models      import session_model  # noqa: registers ORM model with Base

print(f'Initialising database: {engine.url}')
init_db()
print('✅ Tables created successfully.')