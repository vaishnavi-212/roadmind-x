import h3
from typing import List, Tuple

# Convert lat/lng to H3 cell index
def latlng_to_cell(lat: float, lng: float, resolution: int = 9) -> str:
    return h3.geo_to_h3(lat, lng, resolution)

# Convert H3 cell back to lat/lng center point
def cell_to_latlng(cell: str) -> Tuple[float, float]:
    lat, lng = h3.h3_to_geo(cell)
    return lat, lng

# Get all neighboring cells within k rings
def get_neighbors(cell: str, k: int = 1) -> List[str]:
    return list(h3.k_ring(cell, k))

# Get all cells along a route (list of lat/lng points)
def route_to_cells(coordinates: List[Tuple[float, float]], resolution: int = 9) -> List[str]:
    cells = []
    for lat, lng in coordinates:
        cell = latlng_to_cell(lat, lng, resolution)
        if cell not in cells:
            cells.append(cell)
    return cells

# Get distance between two cells (in grid steps)
def cell_distance(cell1: str, cell2: str) -> int:
    return h3.h3_distance(cell1, cell2)

# Check if a lat/lng point is within a cell
def is_point_in_cell(lat: float, lng: float, cell: str) -> bool:
    point_cell = latlng_to_cell(lat, lng)
    return point_cell == cell