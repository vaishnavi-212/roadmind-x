from sqlalchemy import Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class RoadEvent(Base):
    __tablename__ = "road_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Location
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    h3_cell = Column(String, nullable=False)   # H3 index of this location
    
    # Detection
    hazard_type = Column(String, nullable=False)  # pothole, flood, debris etc
    confidence = Column(Float, nullable=False)     # 0.0 to 1.0
    severity = Column(String, nullable=False)      # low, medium, high
    
    # Memory decay
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    seen_count = Column(Integer, default=1)        # how many users reported this
    decay_score = Column(Float, default=1.0)       # starts at 1.0, decays over time

    # Source
    image_path = Column(String, nullable=True)
    source = Column(String, default="user")        # user, dataset, sensor