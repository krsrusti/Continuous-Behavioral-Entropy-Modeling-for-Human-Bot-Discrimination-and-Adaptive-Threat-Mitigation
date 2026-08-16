"""db.py — SQLAlchemy engine + session factory."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

# Build absolute path to data/tif.db — works on Windows, Mac, Linux
_HERE     = os.path.dirname(os.path.abspath(__file__))
_ROOT     = os.path.abspath(os.path.join(_HERE, '..', '..'))
_DATA_DIR = os.path.join(_ROOT, 'data')
_DB_FILE  = os.path.join(_DATA_DIR, 'tif.db')

# Create the data folder if it doesn't exist yet
os.makedirs(_DATA_DIR, exist_ok=True)

DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{_DB_FILE}')

engine  = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False} if 'sqlite' in DATABASE_URL else {}
)
Session = scoped_session(sessionmaker(bind=engine))
Base    = declarative_base()


def init_db():
    """Create all tables."""
    Base.metadata.create_all(engine)


def get_db():
    """Return the current scoped session."""
    return Session()