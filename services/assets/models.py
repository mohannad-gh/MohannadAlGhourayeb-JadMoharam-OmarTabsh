
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)

    asset_name = db.Column(
        db.String(150), nullable=False
    )

    asset_type = db.Column(
        db.String(80), nullable=False
    )

    ip_address = db.Column(
        db.String(45), nullable=True
    )

    department = db.Column(
        db.String(100), nullable=False
    )

    owner_id = db.Column(
        db.Integer, nullable=False
    )

    criticality = db.Column(
        db.String(20), nullable=False
    )

    status = db.Column(
        db.String(30), nullable=False,
        default="Active"
    )

    created_date = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
