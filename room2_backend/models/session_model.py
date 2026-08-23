"""
session_model.py — SQLAlchemy ORM model for a TIF session.

Design rules:
  - agent_class is NEVER set from the browser payload.
    It is stamped server-side from the experiment lookup.
  - user_agent is stored as metadata only.
    It is explicitly excluded from to_feature_dict().
  - label is kept as a backward-compatible alias for agent_class.
  - probe_enabled, task_id, participant_id, experiment_id
    are required for the experimental design.
"""
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, DateTime, Boolean

from database.db import Base


class SessionModel(Base):
    __tablename__ = 'sessions'

    # ── Identity ──────────────────────────────────────────────────────────────
    session_id      = Column(String(64),  primary_key=True)

    # ── Experiment metadata ───────────────────────────────────────────────────
    experiment_id   = Column(String(64),  nullable=True,  index=True)
    participant_id  = Column(String(64),  nullable=True,  index=True)
    task_id         = Column(String(32),  nullable=True)
    probe_enabled   = Column(Boolean,     nullable=True)

    # ── Ground truth — NEVER from browser ────────────────────────────────────
    agent_class     = Column(String(16),  nullable=True)   # human | bot | llm
    label           = Column(String(16),  nullable=True)   # alias for agent_class

    # ── Page info ─────────────────────────────────────────────────────────────
    page_type       = Column(String(32),  nullable=False, default='unknown')

    # ── Timing ───────────────────────────────────────────────────────────────
    start_time      = Column(Float,       nullable=True)
    end_time        = Column(Float,       nullable=True)

    # ── Telemetry (raw JSON blobs) ────────────────────────────────────────────
    passive_events  = Column(Text,        nullable=True)
    probes          = Column(Text,        nullable=True)

    # ── Metadata (never used as ML feature) ───────────────────────────────────
    user_agent      = Column(Text,        nullable=True)

    # ── Housekeeping ──────────────────────────────────────────────────────────
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # ── Construction ─────────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, d: dict, experiment=None) -> 'SessionModel':
        """
        Build a SessionModel from a browser payload dict.

        agent_class is NEVER taken from d — always from the experiment object.
        If no experiment is provided, agent_class stays null until labelled manually.

        Args:
            d:          browser payload dict
            experiment: ExperimentModel instance (optional)
        """
        # Resolve agent_class from experiment — never from browser
        agent_class = None
        if experiment is not None:
            agent_class = experiment.agent_class

        # probe_enabled from experiment takes priority over browser claim
        probe_enabled = None
        if experiment is not None:
            probe_enabled = experiment.probe_enabled
        elif 'probe_enabled' in d:
            probe_enabled = bool(d['probe_enabled'])

        return cls(
            session_id     = d.get('session_id', ''),
            experiment_id  = d.get('experiment_id'),
            participant_id = d.get('participant_id') or (experiment.participant_id if experiment else None),
            task_id        = d.get('task_id') or (experiment.task_id if experiment else None),
            probe_enabled  = probe_enabled,
            agent_class    = agent_class,
            label          = agent_class,   # keep in sync
            page_type      = d.get('page_type', 'unknown'),
            start_time     = d.get('start_time'),
            end_time       = d.get('end_time'),
            passive_events = json.dumps(d.get('passive_events', [])),
            probes         = json.dumps(d.get('probes', [])),
            user_agent     = d.get('user_agent'),   # metadata only
        )

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Full session dict including metadata.
        Used for API responses and the labelling dashboard.
        user_agent is included but clearly in the metadata section.
        """
        return {
            # Identity
            'session_id':     self.session_id,

            # Experiment metadata
            'experiment_id':  self.experiment_id,
            'participant_id': self.participant_id,
            'task_id':        self.task_id,
            'probe_enabled':  self.probe_enabled,

            # Ground truth
            'agent_class':    self.agent_class,
            'label':          self.label,

            # Page
            'page_type':      self.page_type,

            # Timing
            'start_time':     self.start_time,
            'end_time':       self.end_time,

            # Telemetry
            'passive_events': json.loads(self.passive_events or '[]'),
            'probes':         json.loads(self.probes         or '[]'),

            # Metadata — clearly separated
            '_metadata': {
                'user_agent':  self.user_agent,
                'created_at':  self.created_at.isoformat() if self.created_at else None,
            },
        }

    def to_feature_dict(self) -> dict:
        """
        Feature-safe dict — explicitly excludes all metadata.
        This is what should be passed to the feature extractor.

        NEVER includes: user_agent, participant_id, experiment_id,
                        session_id, agent_class, label
        """
        return {
            'task_id':        self.task_id,
            'probe_enabled':  self.probe_enabled,
            'page_type':      self.page_type,
            'start_time':     self.start_time,
            'end_time':       self.end_time,
            'passive_events': json.loads(self.passive_events or '[]'),
            'probes':         json.loads(self.probes         or '[]'),
        }

    def sync_label(self):
        """Keep label and agent_class in sync."""
        if self.agent_class and not self.label:
            self.label = self.agent_class
        elif self.label and not self.agent_class:
            self.agent_class = self.label

    def __repr__(self):
        return (f'<Session {self.session_id[:8]} '
                f'agent={self.agent_class} '
                f'task={self.task_id} '
                f'probe={self.probe_enabled}>')