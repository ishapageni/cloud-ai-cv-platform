import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    filename = Column(
        String(255),
        nullable=False,
    )

    status = Column(
        String(50),
        nullable=False,
    )

    model = Column(
        String(100),
        nullable=False,
        default="YOLO11n",
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    result_object_key = Column(
        String(500),
        nullable=True,
    )

    detections = relationship(
        "Detection",
        back_populates="job",
        cascade="all, delete-orphan",
    )


class Detection(Base):
    __tablename__ = "detections"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "jobs.job_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    class_id = Column(
        Integer,
        nullable=False,
    )

    class_name = Column(
        String(100),
        nullable=False,
    )

    confidence = Column(
        Float,
        nullable=False,
    )

    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)

    job = relationship(
        "Job",
        back_populates="detections",
    )
