"""
experiment_model.py — SQLAlchemy ORM model for a TIF experiment.

An experiment record is created BEFORE the browser session starts.
It holds the ground truth that the browser must never know:
  - agent_class (human | bot | llm)

It also holds the experimental conditions:
  - task_id       (login | checkout | search | navigation)
  - probe_enabled (true | false)
  - participant_id (anonymous, backend-generated)

When a session arrives at POST /api/session, the backend:
  1. Looks up the experiment by experiment_id
  2. Stamps agent_class from the experiment onto the session
  3. Verifies probe_enabled matches the experiment record

The browser only ever receives:
  - experiment_id
  - participant_id
  - task_id
  - probe_enabled

The browser NEVER receives:
  - agent_class
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text

from database.db import Base


# ── Valid values ──────────────────────────────────────────────────────────────

VALID_AGENT_CLASSES = {'human', 'bot', 'llm'}
VALID_TASK_IDS      = {'login', 'checkout', 'search', 'navigation'}


class ExperimentModel(Base):
    __tablename__ = 'experiments'

    # ── Identity ──────────────────────────────────────────────────────────────
    experiment_id   = Column(String(64), primary_key=True,
                             default=lambda: f'exp_{uuid.uuid4().hex[:12]}')

    # ── Participant ───────────────────────────────────────────────────────────
    # Anonymous, backend-generated. Never reused across agent classes.
    participant_id  = Column(String(64), nullable=False,
                             default=lambda: f'p_{uuid.uuid4().hex[:12]}')

    # ── Ground truth — set by researcher, NEVER sent to browser ──────────────
    agent_class     = Column(String(16), nullable=False)   # human | bot | llm

    # ── Experimental conditions ───────────────────────────────────────────────
    task_id         = Column(String(32), nullable=False)   # login | checkout | search | navigation
    probe_enabled   = Column(Boolean,    nullable=False)   # true | false

    # ── Status ────────────────────────────────────────────────────────────────
    # Tracks whether the session was submitted for this experiment
    session_id      = Column(String(64), nullable=True)    # filled when session arrives
    completed       = Column(Boolean,    default=False)

    # ── Researcher notes ──────────────────────────────────────────────────────
    notes           = Column(Text,       nullable=True)

    # ── Housekeeping ──────────────────────────────────────────────────────────
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at    = Column(DateTime, nullable=True)

    # ── Construction ─────────────────────────────────────────────────────────

    @classmethod
    def create(cls,
               agent_class:   str,
               task_id:       str,
               probe_enabled: bool,
               notes:         str = None) -> 'ExperimentModel':
        """
        Create a new experiment record.

        Args:
            agent_class:   'human' | 'bot' | 'llm'
            task_id:       'login' | 'checkout' | 'search' | 'navigation'
            probe_enabled: True | False
            notes:         optional researcher notes

        Raises:
            ValueError if agent_class or task_id are invalid
        """
        if agent_class not in VALID_AGENT_CLASSES:
            raise ValueError(
                f'agent_class must be one of {VALID_AGENT_CLASSES}, got: {agent_class}'
            )
        if task_id not in VALID_TASK_IDS:
            raise ValueError(
                f'task_id must be one of {VALID_TASK_IDS}, got: {task_id}'
            )

        return cls(
            agent_class   = agent_class,
            task_id       = task_id,
            probe_enabled = probe_enabled,
            notes         = notes,
        )

    def mark_completed(self, session_id: str):
        """Mark experiment as completed when session is received."""
        self.session_id   = session_id
        self.completed    = True
        self.completed_at = datetime.now(timezone.utc)

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_browser_dict(self) -> dict:
        """
        Safe dict to return to the browser.
        NEVER includes agent_class.
        """
        return {
            'experiment_id':  self.experiment_id,
            'participant_id': self.participant_id,
            'task_id':        self.task_id,
            'probe_enabled':  self.probe_enabled,
            # agent_class intentionally omitted
        }

    def to_dict(self) -> dict:
        """
        Full dict for researcher dashboard and internal use only.
        Includes agent_class.
        """
        return {
            'experiment_id':  self.experiment_id,
            'participant_id': self.participant_id,
            'agent_class':    self.agent_class,
            'task_id':        self.task_id,
            'probe_enabled':  self.probe_enabled,
            'session_id':     self.session_id,
            'completed':      self.completed,
            'notes':          self.notes,
            'created_at':     self.created_at.isoformat() if self.created_at else None,
            'completed_at':   self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return (f'<Experiment {self.experiment_id} '
                f'agent={self.agent_class} '
                f'task={self.task_id} '
                f'probe={self.probe_enabled} '
                f'completed={self.completed}>')