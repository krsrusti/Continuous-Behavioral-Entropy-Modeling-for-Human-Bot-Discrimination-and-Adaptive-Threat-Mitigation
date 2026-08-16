"""Export all sessions from DB to data/sessions/ as JSON files."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../room2_backend'))
from database.db import get_db
from models.session_model import SessionModel

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), '../data/sessions')
os.makedirs(SESSIONS_DIR, exist_ok=True)

db       = get_db()
sessions = db.query(SessionModel).all()

for s in sessions:
    if not s.label:
        print(f'Skipping unlabelled session {s.session_id[:8]}')
        continue
    path = os.path.join(SESSIONS_DIR, f'{s.label}_{s.session_id[:8]}.json')
    with open(path, 'w') as f:
        json.dump(s.to_dict(), f, indent=2)

print(f'Exported {len(sessions)} sessions → {SESSIONS_DIR}')