import httpx
import logging
from typing import List
from finshield.config.settings import settings

logger = logging.getLogger(__name__)

class EmbeddingError(Exception):
    pass

class MistralEmbeddingService:
    """
    Dedicated service for embedding text via the Mistral REST API.
    Uses 'mistral-embed' which has a vector dimension of 1024.
    """
    def __init__(self):
        if not settings.mistral_api_key:
            raise EmbeddingError("MISTRAL_API_KEY is not configured in .env")
        
        self.api_key = settings.mistral_api_key
        self.api_url = "https://api.mistral.ai/v1/embeddings"
        self.model = "mistral-embed"
        self.dimension = 1024

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a batch of texts.
        """
        if not texts:
            return []
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": texts
        }
        
        try:
            # Setting longer timeout for batch requests
            with httpx.Client(timeout=60.0) as client:
                response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # The response 'data' contains objects with an 'embedding' list of floats
                embeddings = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
                return embeddings
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Mistral API returned an error: {e.response.text}")
            raise EmbeddingError(f"Mistral API error: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"Failed to communicate with Mistral API: {e}")
            raise EmbeddingError(f"Embedding failure: {str(e)}") from e

    def embed_text(self, text: str) -> List[float]:
        """
        Embeds a single string.
        """
        return self.embed_batch([text])[0]
