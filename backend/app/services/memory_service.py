import redis
import json
from datetime import datetime, timedelta
from typing import List, Optional
from app.core.config import settings
from app.utils.h3_utils import latlng_to_cell, get_neighbors

r = redis.from_url(settings.REDIS_URL)

# How long before a hazard fully decays (in hours)
DECAY_WINDOW_HOURS = 6

def compute_decay_score(last_seen: str, seen_count: int) -> float:
    """
    Recency + frequency based decay.
    Recent sightings by many users = high score.
    Old sightings by one user = near zero.
    """
    last_seen_dt = datetime.fromisoformat(last_seen)
    hours_passed = (datetime.utcnow() - last_seen_dt).total_seconds() / 3600
    
    # Time decay: drops to 0 over DECAY_WINDOW_HOURS
    time_factor = max(0.0, 1.0 - (hours_passed / DECAY_WINDOW_HOURS))
    
    # Frequency boost: more reports = more confidence, capped at 1.0
    frequency_factor = min(1.0, seen_count / 5.0)
    
    # Final score weighted 70% time, 30% frequency
    return round((0.7 * time_factor) + (0.3 * frequency_factor), 3)


def store_hazard(lat: float, lng: float, hazard_type: str,
                 confidence: float, severity: str) -> dict:
    """
    Store a detected hazard into Redis memory.
    If same cell already has this hazard, update it instead of duplicating.
    """
    cell = latlng_to_cell(lat, lng, settings.H3_RESOLUTION)
    key = f"hazard:{cell}:{hazard_type}"

    existing = r.get(key)

    if existing:
        data = json.loads(existing)
        data["seen_count"] += 1
        data["last_seen"] = datetime.utcnow().isoformat()
        data["confidence"] = max(data["confidence"], confidence)
        data["severity"] = severity
        data["decay_score"] = compute_decay_score(
            data["last_seen"], data["seen_count"]
        )
    else:
        data = {
            "cell": cell,
            "lat": lat,
            "lng": lng,
            "hazard_type": hazard_type,
            "confidence": confidence,
            "severity": severity,
            "created_at": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat(),
            "seen_count": 1,
            "decay_score": compute_decay_score(
                datetime.utcnow().isoformat(), 1
            )
        }

    # Store in Redis with expiry of DECAY_WINDOW_HOURS
    r.setex(key, timedelta(hours=DECAY_WINDOW_HOURS), json.dumps(data))
    return data


def get_hazards_for_cell(cell: str) -> List[dict]:
    """
    Get all active hazards for a given H3 cell.
    """
    pattern = f"hazard:{cell}:*"
    keys = r.keys(pattern)
    hazards = []
    for key in keys:
        raw = r.get(key)
        if raw:
            hazards.append(json.loads(raw))
    return hazards


def get_hazards_for_route(cells: List[str]) -> List[dict]:
    """
    Get all hazards along a route (list of H3 cells).
    Also checks neighboring cells for nearby hazards.
    """
    all_hazards = []
    checked = set()

    for cell in cells:
        nearby = get_neighbors(cell, k=1)
        for c in [cell] + nearby:
            if c not in checked:
                checked.add(c)
                all_hazards.extend(get_hazards_for_cell(c))

    # Sort by decay score descending (most relevant first)
    all_hazards.sort(key=lambda x: x["decay_score"], reverse=True)
    return all_hazards


def get_hazard_summary(cells: List[str]) -> dict:
    """
    Returns a risk summary for a route.
    """
    hazards = get_hazards_for_route(cells)
    if not hazards:
        return {"risk_level": "clear", "hazard_count": 0, "hazards": []}

    avg_score = sum(h["decay_score"] for h in hazards) / len(hazards)

    if avg_score > 0.7:
        risk = "high"
    elif avg_score > 0.4:
        risk = "medium"
    else:
        risk = "low"

    return {
        "risk_level": risk,
        "hazard_count": len(hazards),
        "avg_decay_score": round(avg_score, 3),
        "hazards": hazards
    }