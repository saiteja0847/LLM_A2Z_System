"""AI Lab client."""
import requests
from typing import Optional
from .models import ModelManager
from .chat import ChatClient
from .training import TrainingManager


class AILabClient:
    """
    Main client for AI Lab platform.

    Args:
        base_url: Base URL of AI Lab API (default: http://localhost:8000)
        timeout: Request timeout in seconds (default: 30)

    Example:
        >>> client = AILabClient("http://localhost:8000")
        >>> models = client.models.list()
        >>> response = client.chat.complete("qwen-1-5b", [{"role": "user", "content": "Hi"}])
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        # Initialize managers
        self.models = ModelManager(self)
        self.chat = ChatClient(self)
        self.training = TrainingManager(self)

    def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[dict] = None,
        files: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> requests.Response:
        """
        Make HTTP request to API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json: JSON body data
            files: Files to upload
            params: Query parameters

        Returns:
            Response object

        Raises:
            requests.HTTPError: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        response = self.session.request(
            method=method,
            url=url,
            json=json,
            files=files,
            params=params,
            timeout=self.timeout,
        )

        response.raise_for_status()
        return response

    def get(self, endpoint: str, params: Optional[dict] = None) -> requests.Response:
        """Make GET request."""
        return self._request("GET", endpoint, params=params)

    def post(
        self,
        endpoint: str,
        json: Optional[dict] = None,
        files: Optional[dict] = None,
    ) -> requests.Response:
        """Make POST request."""
        return self._request("POST", endpoint, json=json, files=files)

    def delete(self, endpoint: str) -> requests.Response:
        """Make DELETE request."""
        return self._request("DELETE", endpoint)

    def health_check(self) -> dict:
        """
        Check API health.

        Returns:
            Health status dict

        Example:
            >>> client = AILabClient()
            >>> health = client.health_check()
            >>> print(health["status"])
            healthy
        """
        response = self.get("/health")
        return response.json()

    def __repr__(self) -> str:
        return f"AILabClient(base_url='{self.base_url}')"
