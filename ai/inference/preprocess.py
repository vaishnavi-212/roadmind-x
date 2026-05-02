import cv2
import numpy as np
from PIL import Image
import io
from typing import Union

# Target size for YOLO input
IMG_SIZE = 640

def load_image_from_bytes(image_bytes: bytes) -> np.ndarray:
    """
    Load image from raw bytes (from API upload).
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(image)


def load_image_from_path(path: str) -> np.ndarray:
    """
    Load image from file path.
    """
    image = cv2.imread(path)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def resize_image(image: np.ndarray) -> np.ndarray:
    """
    Resize image to YOLO input size.
    """
    return cv2.resize(image, (IMG_SIZE, IMG_SIZE))


def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    Normalize pixel values to 0-1 range.
    """
    return image.astype(np.float32) / 255.0


def preprocess(image_input: Union[bytes, str, np.ndarray]) -> np.ndarray:
    """
    Full preprocessing pipeline.
    Accepts bytes (API upload), file path, or raw numpy array.
    Returns normalized numpy array ready for YOLO.
    """
    if isinstance(image_input, bytes):
        image = load_image_from_bytes(image_input)
    elif isinstance(image_input, str):
        image = load_image_from_path(image_input)
    elif isinstance(image_input, np.ndarray):
        image = image_input
    else:
        raise ValueError(f"Unsupported input type: {type(image_input)}")

    image = resize_image(image)
    image = normalize_image(image)
    return image


def preprocess_batch(images: list) -> np.ndarray:
    """
    Preprocess a batch of images.
    Returns stacked numpy array of shape (N, 640, 640, 3).
    """
    return np.stack([preprocess(img) for img in images])