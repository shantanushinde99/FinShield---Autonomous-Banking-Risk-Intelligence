import httpx
import logging
from typing import Dict, Any, Type
from pydantic import BaseModel
import json
from finshield.config.settings import settings

logger = logging.getLogger(__name__)

class LLMServiceError(Exception):
    pass

class MistralLLMService:
    """
    Abstractions for Mistral LLM to generate structured JSON outputs.
    """
    def __init__(self):
        if not settings.mistral_api_key:
            raise LLMServiceError("MISTRAL_API_KEY is not configured in .env")
        
        self.api_key = settings.mistral_api_key
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        self.model = "open-mistral-7b"

    @staticmethod
    def _is_valid_for_schema(data: dict, schema_class: Type[BaseModel]) -> bool:
        """Check if a dict has enough required fields to match the schema."""
        required_fields = set(schema_class.model_fields.keys())
        data_keys = set(data.keys())
        # If at least half of required fields are present, it's likely the right level
        overlap = required_fields & data_keys
        return len(overlap) >= len(required_fields) * 0.5

    def generate_structured_response(self, prompt: str, schema_class: Type[BaseModel]) -> BaseModel:
        """
        Sends a prompt to Mistral and expects a JSON response adhering to the Pydantic schema.
        """
        system_prompt = (
            "You are an expert banking risk analyst. "
            "You MUST output your final answer as raw JSON matching the following schema. "
            "CRITICAL: Do NOT put positive factors or risk factors inside the 'explanation' string. "
            "You MUST put them as strings inside the 'positive_factors' and 'risk_factors' JSON arrays. "
            "Keep the 'explanation' string concise (2-3 sentences max) as a high-level summary only. "
            "Do NOT wrap the JSON in Markdown block quotes (like ```json), just return the raw JSON object.\n"
            f"Schema:\n{schema_class.model_json_schema()}"
        )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                content = data["choices"][0]["message"]["content"]
                
                # Parse JSON and validate against Pydantic schema
                try:
                    parsed_json = json.loads(content)
                    
                    # LLMs sometimes wrap the response in extra nesting, e.g.:
                    # {"$schema": "...", "RiskAssessment": {...actual fields...}}
                    # or {"risk_assessment": {...}}
                    # We need to unwrap it to get the actual fields.
                    if not self._is_valid_for_schema(parsed_json, schema_class):
                        # Try to find the actual data nested under a key
                        for key, value in parsed_json.items():
                            if isinstance(value, dict) and self._is_valid_for_schema(value, schema_class):
                                logger.info(f"Unwrapped LLM response from nested key '{key}'")
                                parsed_json = value
                                break
                    
                    return schema_class(**parsed_json)
                except Exception as e:
                    logger.error(f"Failed to parse or validate LLM JSON response: {content}")
                    raise LLMServiceError(f"LLM produced invalid structured output: {e}")
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"Mistral API error: {e.response.text}")
            raise LLMServiceError(f"Mistral API returned status {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"LLM Service failure: {e}")
            raise LLMServiceError(f"Failed to communicate with LLM: {e}") from e
