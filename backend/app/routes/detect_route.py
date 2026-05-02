from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.memory_service import store_hazard, get_hazard_summary
from app.utils.h3_utils import route_to_cells
from ai.inference.detect import RoadHazardDetector
from app.core.config import settings
import json

router = APIRouter(prefix="/api", tags=["detection"])

# Initialize detector once at startup
detector = RoadHazardDetector(
    model_path=settings.MODEL_PATH,
    confidence_threshold=settings.CONFIDENCE_THRESHOLD
)


@router.post("/detect")
async def detect_hazard(
    file: UploadFile = File(...),
    lat: float = Form(...),
    lng: float = Form(...),
):
    """
    Upload a road image with GPS coordinates.
    Detects hazards and stores them in spatial memory.
    """
    try:
        image_bytes = await file.read()
        detections = detector.detect(image_bytes)

        if not detections:
            return {
                "status": "ok",
                "message": "No hazards detected",
                "detections": []
            }

        stored = []
        for det in detections:
            result = store_hazard(
                lat=lat,
                lng=lng,
                hazard_type=det["hazard_type"],
                confidence=det["confidence"],
                severity=det["severity"]
            )
            stored.append(result)

        return {
            "status": "ok",
            "message": f"{len(stored)} hazard(s) detected and stored",
            "location": {"lat": lat, "lng": lng},
            "detections": stored
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/route-check")
async def check_route(coordinates: list):
    """
    Submit a list of lat/lng points for a planned route.
    Returns hazard summary along that route.
    """
    try:
        coords = [(point["lat"], point["lng"]) for point in coordinates]
        cells = route_to_cells(coords, resolution=settings.H3_RESOLUTION)
        summary = get_hazard_summary(cells)

        return {
            "status": "ok",
            "route_cells_checked": len(cells),
            "summary": summary
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hazards/{lat}/{lng}")
async def get_nearby_hazards(lat: float, lng: float):
    """
    Get all active hazards near a given location.
    """
    try:
        from app.utils.h3_utils import latlng_to_cell, get_neighbors
        from app.services.memory_service import get_hazards_for_cell

        cell = latlng_to_cell(lat, lng, settings.H3_RESOLUTION)
        neighbors = get_neighbors(cell, k=1)

        all_hazards = []
        for c in [cell] + neighbors:
            all_hazards.extend(get_hazards_for_cell(c))

        return {
            "status": "ok",
            "location": {"lat": lat, "lng": lng},
            "hazard_count": len(all_hazards),
            "hazards": all_hazards
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))