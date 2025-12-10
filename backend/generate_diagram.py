#!/usr/bin/env python3
"""
Generate database diagram from SQLAlchemy models
"""
import os

os.environ["DATABASE_URL"] = (
    "sqlite:///:memory:"  # Use in-memory DB to avoid connection issues
)

from app.models import Base
from eralchemy import render_er

# Generate PNG diagram
render_er(Base, "database_diagram.png")
print("✅ Database diagram generated: database_diagram.png")
