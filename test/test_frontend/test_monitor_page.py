"""
Frontend Monitor Page Tests
Tests for the browser monitoring page functionality
"""
import pytest
import requests
import time
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

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


class TestMonitorPage:
    """Test cases for monitor page functionality"""

    @pytest.fixture(scope="class")
    def driver(self):
        """Setup Chrome driver for testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)
        yield driver
        driver.quit()

    def test_page_load(self, driver):
        """Test that monitor page loads successfully"""
        _require_server()
        driver.get(f"{BASE_URL}/monitor/monitor.html")
        assert "AR监控系统" in driver.title

    def test_websocket_connection(self, driver):
        """Test WebSocket connection establishment"""
        _require_server()
        driver.get(f"{BASE_URL}/monitor/monitor.html")

        # Wait for WebSocket connection indicator
        wait = WebDriverWait(driver, 10)
        connection_status = wait.until(
            EC.presence_of_element_located((By.ID, "connection-status"))
        )
        assert connection_status.text

    def test_module_cards_display(self, driver):
        """Test that module cards are displayed"""
        _require_server()
        driver.get(f"{BASE_URL}/monitor/monitor.html")

        wait = WebDriverWait(driver, 10)
        module_cards = wait.until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "nav-item"))
        )
        assert len(module_cards) > 0

    def test_api_health_check(self):
        """Test API health check endpoint"""
        _require_server()
        response = SESSION.get(f"{BASE_URL}{API_PREFIX}/health" if API_PREFIX else f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (dict, list))

    def test_system_monitor_data(self):
        """Test system monitor API returns data"""
        _require_server()
        response = SESSION.get(f"{BASE_URL}{API_PREFIX}/overview" if API_PREFIX else f"{BASE_URL}/overview")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (dict, list))

    def test_page_responsive_design(self, driver):
        """Test responsive design on different screen sizes"""
        _require_server()
        driver.get(f"{BASE_URL}/monitor/monitor.html")

        # Test mobile size
        driver.set_window_size(375, 667)
        time.sleep(1)
        assert driver.find_element(By.TAG_NAME, "body").is_displayed()

        # Test tablet size
        driver.set_window_size(768, 1024)
        time.sleep(1)
        assert driver.find_element(By.TAG_NAME, "body").is_displayed()

        # Test desktop size
        driver.set_window_size(1920, 1080)
        time.sleep(1)
        assert driver.find_element(By.TAG_NAME, "body").is_displayed()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
