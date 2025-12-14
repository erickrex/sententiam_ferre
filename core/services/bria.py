"""
BRIA FIBO API client for image generation.

This module provides the BriaClient class for communicating with BRIA's
FIBO (structured JSON) text-to-image generation API.
"""
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
import requests
from decouple import config

logger = logging.getLogger(__name__)


class GenerationStatus(Enum):
    """Status of a BRIA generation request."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class GenerationResult:
    """Result of a generation status check."""
    status: GenerationStatus
    image_url: Optional[str] = None
    error_message: Optional[str] = None
    fibo_json: Optional[Dict[str, Any]] = field(default=None)  # Structured JSON inferred by FIBO


class BriaClientError(Exception):
    """Base exception for BRIA client errors."""
    pass


class BriaAuthenticationError(BriaClientError):
    """Raised when API authentication fails."""
    pass


class BriaRateLimitError(BriaClientError):
    """Raised when API rate limit is exceeded."""
    pass


class BriaServerError(BriaClientError):
    """Raised when BRIA API returns a server error."""
    pass


class BriaClient:
    """
    Client for BRIA's FIBO text-to-image generation API (V2).
    
    FIBO uses a two-step process:
    1. VLM Bridge translates text/images into a structured_prompt (JSON)
    2. FIBO image model generates the final image from the structured_prompt
    
    This client uses the all-in-one /image/generate endpoint which handles
    both steps automatically.
    
    This client handles:
    - Submitting generation requests to the FIBO V2 endpoint
    - Capturing and logging the structured JSON inferred from prompts
    - Polling for completion status
    - Downloading generated images
    
    The API token is retrieved from the BRIA_API_TOKEN environment variable.
    """
    
    BASE_URL = "https://engine.prod.bria-api.com/v2"
    # FIBO V2 all-in-one endpoint (VLM bridge + image generation)
    FIBO_ENDPOINT = "/image/generate"
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize the BRIA client.
        
        Args:
            api_token: Optional API token. If not provided, reads from
                      BRIA_API_TOKEN environment variable or .env file.
        
        Raises:
            BriaClientError: If no API token is available.
        """
        self.api_token = api_token or config("BRIA_API_TOKEN", default=None)
        if not self.api_token:
            raise BriaClientError(
                "BRIA API token not found. Set BRIA_API_TOKEN environment variable."
            )
        self._session = requests.Session()
        self._session.headers.update({
            "api_token": self.api_token,
            "Content-Type": "application/json"
        })
    
    def generate(self, prompt: str, num_results: int = 1, sync: bool = False) -> str:
        """
        Submit a generation request to the BRIA FIBO V2 API.
        
        FIBO uses a VLM Bridge to translate the prompt into structured JSON,
        then generates the image from that structured representation.
        
        Args:
            prompt: The text prompt describing the image to generate.
            num_results: Number of images to generate (default: 1, currently unused by FIBO v2).
            sync: Whether to wait for completion (default: False, currently unused by FIBO v2).
        
        Returns:
            The request_id for polling status (async) or tuple of (request_id, image_url, fibo_json) (sync).
        
        Raises:
            BriaAuthenticationError: If API authentication fails.
            BriaRateLimitError: If rate limit is exceeded.
            BriaServerError: If BRIA API returns a server error.
            BriaClientError: For other API errors.
        """
        url = f"{self.BASE_URL}{self.FIBO_ENDPOINT}"
        
        # FIBO v2 API with sync mode for immediate response
        payload = {
            "prompt": prompt,
            "model_version": "FIBO",
            "sync": True,  # Get result immediately instead of polling
        }
        
        print("=" * 60)
        print("BRIA FIBO V2 Generation Request (SYNC MODE)")
        print("=" * 60)
        print(f"Prompt: {prompt[:100]}...")
        print(f"Endpoint: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            # FIBO v2 sync mode can take up to 120 seconds to generate
            response = self._session.post(url, json=payload, timeout=120)
            print(f"Response status code: {response.status_code}")
            self._handle_response_errors(response)
            
            data = response.json()
            
            # Log the full FIBO response
            print("-" * 60)
            print("BRIA FIBO V2 Response:")
            print("-" * 60)
            print(json.dumps(data, indent=2))
            
            # Extract FIBO structured JSON if present
            fibo_json = self._extract_fibo_json(data)
            if fibo_json:
                print("-" * 60)
                print("FIBO Inferred Structured JSON:")
                print("-" * 60)
                print(json.dumps(fibo_json, indent=2))
            
            # FIBO v2 sync response format: { result: { image_url, seed, structured_prompt }, request_id }
            image_url = None
            
            print(f"Looking for image_url in response keys: {list(data.keys())}")
            
            # Sync mode returns result object (not array)
            result = data.get("result")
            if result and isinstance(result, dict):
                print(f"Found result object with keys: {list(result.keys())}")
                image_url = result.get("image_url")
                if image_url:
                    print(f"Found image_url in result: {image_url}")
                # Get structured_prompt from result
                structured_prompt = result.get("structured_prompt")
                if structured_prompt:
                    try:
                        fibo_json = json.loads(structured_prompt) if isinstance(structured_prompt, str) else structured_prompt
                    except json.JSONDecodeError:
                        fibo_json = {"raw": structured_prompt}
                seed = result.get("seed")
                if seed:
                    fibo_json = fibo_json or {}
                    fibo_json["seed"] = seed
            # Fallback: check for direct image_url field
            elif "image_url" in data:
                image_url = data["image_url"]
                print(f"Found image_url directly: {image_url}")
            
            if image_url:
                # Sync completion
                seed = result.get("seed") if result and isinstance(result, dict) else None
                request_id = data.get("request_id") or str(seed or "sync_completed")
                print(f"SUCCESS! BRIA FIBO returned image URL: {image_url[:80]}...")
                print("=" * 60)
                return (str(request_id), image_url, fibo_json)
            
            # Async mode fallback - look for request_id for polling
            request_id = data.get("request_id") or data.get("id") or data.get("task_id")
            if not request_id:
                print(f"ERROR: No request_id or image_url found in response. Full response: {data}")
                raise BriaClientError(f"Unexpected response format. Response: {data}")
            
            print(f"FIBO generation request submitted (async), request_id: {request_id}")
            print("=" * 60)
            return request_id
            
        except requests.RequestException as e:
            logger.error(f"Network error communicating with BRIA FIBO API: {e}")
            raise BriaClientError(f"Network error: {e}") from e
    
    def _extract_fibo_json(self, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract the FIBO structured JSON from the API response.
        
        FIBO V2 returns a structured_prompt (JSON) that was inferred by the
        VLM Bridge from the input prompt. This contains detailed scene
        description, style, composition, colors, etc.
        
        Args:
            response_data: The full API response data.
        
        Returns:
            The FIBO structured JSON if present, None otherwise.
        """
        fibo_json = {}
        
        # FIBO V2 returns structured_prompt from VLM Bridge
        if "structured_prompt" in response_data:
            fibo_json = response_data["structured_prompt"]
        elif "fibo" in response_data:
            fibo_json = response_data["fibo"]
        elif "structured_params" in response_data:
            fibo_json = response_data["structured_params"]
        elif "parameters" in response_data:
            fibo_json = response_data["parameters"]
        
        # Also check in result - can be dict (sync) or list (async)
        result = response_data.get("result")
        if result:
            # Handle dict (sync mode) or list (async mode)
            if isinstance(result, dict):
                item = result
            elif isinstance(result, list) and len(result) > 0:
                item = result[0]
            else:
                item = None
            
            if item and isinstance(item, dict):
                if "structured_prompt" in item:
                    fibo_json = item["structured_prompt"]
                elif "fibo" in item:
                    fibo_json = item["fibo"]
                elif "structured_params" in item:
                    fibo_json = item["structured_params"]
                elif "parameters" in item:
                    fibo_json = item["parameters"]
                # Also capture seed and other generation params
                if "seed" in item:
                    if not fibo_json:
                        fibo_json = {}
                    if isinstance(fibo_json, dict):
                        fibo_json["seed"] = item["seed"]
        
        return fibo_json if fibo_json else None
    
    def check_status(self, request_id: str) -> GenerationResult:
        """
        Check the status of a generation request.
        
        Args:
            request_id: The request ID returned from generate().
        
        Returns:
            GenerationResult with status, image_url, and fibo_json if completed.
        
        Raises:
            BriaAuthenticationError: If API authentication fails.
            BriaClientError: For other API errors.
        """
        # FIBO v2 uses /v2/status/{request_id} for polling
        url = f"{self.BASE_URL}/status/{request_id}"
        
        print(f"Checking FIBO status at: {url}")
        print(f"Using headers: {dict(self._session.headers)}")
        
        try:
            response = self._session.get(url, timeout=30)
            print(f"Status check response code: {response.status_code}")
            print(f"Status check response text: {response.text[:500] if response.text else 'empty'}")
            self._handle_response_errors(response)
            
            data = response.json()
            print(f"Status check response: {json.dumps(data, indent=2)}")
            status_str = data.get("status", "").lower()
            
            if status_str == "completed":
                # Try various response formats for image URL
                image_url = None
                
                # Direct image_url field
                if "image_url" in data:
                    image_url = data["image_url"]
                # Result array format
                elif "result" in data:
                    result = data.get("result", [])
                    if result and len(result) > 0:
                        if isinstance(result[0], dict):
                            urls = result[0].get("urls", [])
                            if urls:
                                image_url = urls[0]
                            elif "image_url" in result[0]:
                                image_url = result[0]["image_url"]
                        elif isinstance(result[0], str):
                            image_url = result[0]
                # Images array format
                elif "images" in data:
                    images = data.get("images", [])
                    if images:
                        image_url = images[0] if isinstance(images[0], str) else images[0].get("url")
                
                print(f"COMPLETED! Image URL: {image_url}")
                
                # Extract FIBO JSON
                fibo_json = self._extract_fibo_json(data)
                if fibo_json:
                    print(f"FIBO structured JSON: {json.dumps(fibo_json, indent=2)}")
                
                return GenerationResult(
                    status=GenerationStatus.COMPLETED,
                    image_url=image_url,
                    fibo_json=fibo_json
                )
            
            elif status_str == "failed":
                error_msg = data.get("error", "Unknown error")
                return GenerationResult(
                    status=GenerationStatus.FAILED,
                    error_message=error_msg
                )
            
            elif status_str in ("pending", "in_queue"):
                return GenerationResult(status=GenerationStatus.PENDING)
            
            elif status_str in ("processing", "in_progress"):
                return GenerationResult(status=GenerationStatus.PROCESSING)
            
            else:
                # Unknown status, treat as processing
                logger.warning(f"Unknown BRIA FIBO status: {status_str}")
                return GenerationResult(status=GenerationStatus.PROCESSING)
                
        except requests.RequestException as e:
            logger.error(f"Network error checking BRIA FIBO status: {e}")
            raise BriaClientError(f"Network error: {e}") from e
    
    def download_image(self, image_url: str) -> bytes:
        """
        Download a generated image from BRIA.
        
        Args:
            image_url: The URL of the generated image.
        
        Returns:
            The image data as bytes.
        
        Raises:
            BriaClientError: If download fails.
        """
        logger.info(f"Downloading image from: {image_url}")
        
        try:
            response = requests.get(image_url, timeout=60)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            logger.error(f"Failed to download image: {e}")
            raise BriaClientError(f"Failed to download image: {e}") from e
    
    def _handle_response_errors(self, response: requests.Response) -> None:
        """
        Handle HTTP error responses from the BRIA API.
        
        Args:
            response: The HTTP response object.
        
        Raises:
            BriaAuthenticationError: For 401 errors.
            BriaRateLimitError: For 429 errors.
            BriaServerError: For 5xx errors.
            BriaClientError: For other error responses.
        """
        if response.status_code == 401:
            logger.error("BRIA API authentication failed")
            raise BriaAuthenticationError("Invalid API token")
        
        if response.status_code == 429:
            logger.warning("BRIA API rate limit exceeded")
            raise BriaRateLimitError("Rate limit exceeded")
        
        if response.status_code >= 500:
            logger.error(f"BRIA API server error: {response.status_code}")
            raise BriaServerError(f"Server error: {response.status_code}")
        
        if not response.ok:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", response.text)
            except ValueError:
                error_msg = response.text
            
            logger.error(f"BRIA API error: {error_msg}")
            raise BriaClientError(f"API error: {error_msg}")
