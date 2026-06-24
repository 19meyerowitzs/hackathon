"""
SQLAlchemy models for Reputation Intelligence App.
"""
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy.sql import func
from .database import Base


class ReputationReport(Base):
    """Model for storing Reputation Intelligence Reports."""
    
    __tablename__ = "reputation_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String, unique=True, nullable=False, index=True)  # UUID
    period = Column(String, nullable=False, index=True)  # e.g. "März 2026"
    company = Column(String, nullable=False, default="OMG Germany", index=True)
    source_files = Column(Text, nullable=True)  # comma-separated filenames
    report_json = Column(Text, nullable=False)  # full JSON string
    html_output = Column(Text, nullable=False)  # rendered HTML
    northstar_score = Column(Integer, nullable=True, index=True)  # quick access KPI
    created_by = Column(String(50), nullable=True)  # API key hint or user
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<ReputationReport(id={self.report_id}, period={self.period}, score={self.northstar_score})>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "report_id": self.report_id,
            "period": self.period,
            "company": self.company,
            "source_files": self.source_files,
            "northstar_score": self.northstar_score,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
        }
