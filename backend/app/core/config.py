from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # App
    APP_NAME: str = "RoadMind-X"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/roadmindx"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Kafka
    KAFKA_BROKER: str = "localhost:9092"
    KAFKA_TOPIC: str = "road-events"

    # AI Model
    MODEL_PATH: str = "ai/model/weights/yolov8n.pt"
    CONFIDENCE_THRESHOLD: float = 0.5

    # H3 resolution (7 = ~5km², good for road segments)
    H3_RESOLUTION: int = 9

    class Config:
        env_file = ".env"

settings = Settings()