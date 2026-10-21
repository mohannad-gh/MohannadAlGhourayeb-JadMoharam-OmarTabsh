
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Vulnerability(db.Model):
    __tablename__ = "vulnerabilities"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    cve_id = db.Column(
        db.String(30),
        nullable=True
    )

    asset_id = db.Column(
        db.Integer,
        nullable=False
    )

    severity = db.Column(
        db.String(20),
        nullable=False
    )

    cvss_score = db.Column(
        db.Float,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Open"
    )

    remediation = db.Column(
        db.Text,
        nullable=True
    )

    discovered_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    updated_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
