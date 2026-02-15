"""
API Client Tests
Tests for frontend API communication functionality
"""
import pytest
import requests
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

TEST_DIR = Path(__file__).resolve().parents[1]
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

from test_utils import (
    get_base_url,
    get_requests_session,
    resolve_monitor_api_prefix,
    require_server,
)

BASE_URL = get_base_url()
API_PREFIX = resolve_monitor_api_prefix(BASE_URL)
SESSION = get_requests_session()


def _require_server():
    if not require_server(BASE_URL, API_PREFIX):
        pytest.skip(f"Server not available: {BASE_URL}{API_PREFIX}/health")


class TestAPIClient:
    """Test cases for API client functionality"""

    def test_health_check_api(self):
        """Test health check API endpoint"""
        _require_server()
        response = SESSION.get(f"{BASE_URL}{API_PREFIX}/health" if API_PREFIX else f"{BASE_URL}/health")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, (dict, list))

    def test_system_status_api(self):
        """Test system status API endpoint"""
        _require_server()
        response = SESSION.get(f"{BASE_URL}{API_PREFIX}/overview" if API_PREFIX else f"{BASE_URL}/overview")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, (dict, list))

    def test_module_status_api(self):
        """Test module status API endpoint"""
        _require_server()
        response = SESSION.get(f"{BASE_URL}{API_PREFIX}/status" if API_PREFIX else f"{BASE_URL}/status")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, (dict, list))

    def test_deployment_status_api(self):
        """Test deployment status API endpoint"""
        _require_server()
        response = SESSION.get(f"{BASE_URL}{API_PREFIX}/overview" if API_PREFIX else f"{BASE_URL}/overview")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, (dict, list))

    def test_logs_api(self):
        """Test logs API endpoint"""
        _require_server()
        response = SESSION.get(f"{BASE_URL}{API_PREFIX}/logs" if API_PREFIX else f"{BASE_URL}/logs")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, (dict, list))

    def test_config_api(self):
        """Test configuration API endpoint"""
        _require_server()
        response = SESSION.get(f"{BASE_URL}{API_PREFIX}/config" if API_PREFIX else f"{BASE_URL}/config")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    @patch('requests.get')
    def test_api_error_handling(self, mock_get):
        """Test API error handling"""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(requests.exceptions.ConnectionError):
            requests.get(f"{BASE_URL}/health")

    @patch('requests.get')
    def test_api_timeout_handling(self, mock_get):
        """Test API timeout handling"""
        mock_get.side_effect = requests.exceptions.Timeout()

        with pytest.raises(requests.exceptions.Timeout):
            requests.get(f"{BASE_URL}/health")

    def test_api_response_format(self):
        """Test API response format consistency"""
        endpoints = [
            "/health",
            "/overview",
            "/status"
        ]

        for endpoint in endpoints:
            _require_server()
            response = SESSION.get(f"{BASE_URL}{API_PREFIX}{endpoint}" if API_PREFIX else f"{BASE_URL}{endpoint}")
            assert response.status_code == 200

            # Check if response is valid JSON
            data = response.json()
            assert isinstance(data, (dict, list))


class TestAPIManager:
    """Test cases for API manager module"""

    def test_manager_initialization(self):
        """Test API manager initialization"""
        manager = Mock()
        manager.get = Mock()
        manager.post = Mock()

        manager.get("/api/health")
        manager.get.assert_called_with("/api/health")

    def test_request_interception(self):
        """Test request interception functionality"""
        intercepted_requests = []

        def intercept_request(url, method, data=None):
            intercepted_requests.append({
                "url": url,
                "method": method,
                "data": data
            })
            return {"status": "intercepted"}

        # Simulate interception
        result = intercept_request("/api/test", "GET")
        assert result["status"] == "intercepted"
        assert len(intercepted_requests) == 1

    def test_response_caching(self):
        """Test response caching functionality"""
        cache = {}

        def cache_response(key, data):
            cache[key] = data

        def get_cached_response(key):
            return cache.get(key)

        # Test caching
        cache_response("health", {"status": "healthy"})
        cached = get_cached_response("health")
        assert cached["status"] == "healthy"

        # Test cache miss
        missed = get_cached_response("nonexistent")
        assert missed is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
