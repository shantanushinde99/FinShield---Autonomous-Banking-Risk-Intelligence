from qdrant_client import QdrantClient
from finshield.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class QdrantConnectionError(Exception):
    pass

def get_qdrant_client() -> QdrantClient:
    """
    Returns a configured instance of QdrantClient using settings from environment variables.
    """
    if not settings.qdrant_url or not settings.qdrant_api_key:
        raise QdrantConnectionError("QDRANT_URL and QDRANT_API_KEY must be configured in .env")

    try:
        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=30.0
        )
        return client
    except Exception as e:
        logger.error(f"Failed to initialize QdrantClient: {e}")
        raise QdrantConnectionError(f"Could not connect to Qdrant: {e}") from e
