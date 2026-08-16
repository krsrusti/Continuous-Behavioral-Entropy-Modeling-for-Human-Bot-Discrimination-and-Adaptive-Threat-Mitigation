"""session_model.py — SQLAlchemy ORM model for a TIF session."""
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, DateTime
from database.db import Base


class SessionModel(Base):
    __tablename__ = 'sessions'

    session_id     = Column(String(64), primary_key=True)
    page_type      = Column(String(32), nullable=False, default='unknown')
    label          = Column(String(16), nullable=True)
    start_time     = Column(Float,      nullable=True)
    end_time       = Column(Float,      nullable=True)
    user_agent     = Column(Text,       nullable=True)
    passive_events = Column(Text,       nullable=True)
    probes         = Column(Text,       nullable=True)
    created_at     = Column(DateTime,   default=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_dict(cls, d: dict) -> 'SessionModel':
        return cls(
            session_id     = d.get('session_id', ''),
            page_type      = d.get('page_type', 'unknown'),
            label          = d.get('label'),
            start_time     = d.get('start_time'),
            end_time       = d.get('end_time'),
            user_agent     = d.get('user_agent'),
            passive_events = json.dumps(d.get('passive_events', [])),
            probes         = json.dumps(d.get('probes', [])),
        )

    def to_dict(self) -> dict:
        return {
            'session_id':     self.session_id,
            'page_type':      self.page_type,
            'label':          self.label,
            'start_time':     self.start_time,
            'end_time':       self.end_time,
            'user_agent':     self.user_agent,
            'passive_events': json.loads(self.passive_events or '[]'),
            'probes':         json.loads(self.probes         or '[]'),
            'created_at':     self.created_at.isoformat() if self.created_at else None,
        }