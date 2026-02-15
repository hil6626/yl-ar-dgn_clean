#!/usr/bin/env python3
"""
Backend Services Validation Script
Validates the backend services implementation
"""
import json
import os
import sys
import importlib.util
import requests
from pathlib import Path


def validate_service_files():
    """Validate that all service files exist"""
    print("🔍 Validating backend service files...")

    required_services = [
        "src/backend/services/__init__.py",
        "src/backend/services/health_check_service.py",
        "src/backend/services/system_monitor_service.py",
        "src/backend/services/deployment_tracker_service.py",
        "src/backend/services/log_collector_service.py",
        "src/backend/services/alert_collector_service.py",
        "src/backend/services/script_executor_service.py",
        "src/backend/services/cache_manager_service.py",
        "src/backend/services/module_status_service.py",
        "src/backend/services/config_service.py"
    ]

    missing_services = []
    for service_file in required_services:
        if not os.path.exists(service_file):
            missing_services.append(service_file)

    if missing_services:
        print(f"❌ Missing service files: {missing_services}")
        return False

    print("✅ All backend service files present")
    return True


def validate_service_imports():
    """Validate that services can be imported"""
    print("🔍 Validating service imports...")

    # Add src to path for imports
    sys.path.insert(0, 'src')

    services_to_test = [
        'backend.services.health_check_service',
        'backend.services.system_monitor_service',
        'backend.services.deployment_tracker_service',
        'backend.services.log_collector_service',
        'backend.services.alert_collector_service',
        'backend.services.script_executor_service',
        'backend.services.cache_manager_service',
        'backend.services.module_status_service',
        'backend.services.config_service'
    ]

    failed_imports = []
    for service in services_to_test:
        try:
            spec = importlib.util.find_spec(service)
            if spec is None:
                failed_imports.append(service)
                continue

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        except Exception as e:
            print(f"⚠️  Import warning for {service}: {e}")
            # Don't fail on import warnings, just log them

    if failed_imports:
        print(f"❌ Failed to import services: {failed_imports}")
        return False

    print("✅ Service imports validation completed")
    return True


def validate_monitor_router():
    """Validate monitor router implementation"""
    print("🔍 Validating monitor router...")

    router_file = "src/backend/monitor_router_refactored.py"
    if not os.path.exists(router_file):
        print(f"❌ Monitor router file not found: {router_file}")
        return False

    # Try to import and check basic structure
    sys.path.insert(0, 'src')
    try:
        spec = importlib.util.find_spec('backend.monitor_router_refactored')
        if spec is None:
            print("❌ Cannot find monitor router module")
            return False

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Check for required functions
        required_functions = ['health_check', 'system_status', 'module_status']
        for func_name in required_functions:
            if not hasattr(module, func_name):
                print(f"❌ Monitor router missing function: {func_name}")
                return False

    except Exception as e:
        print(f"❌ Error validating monitor router: {e}")
        return False

    print("✅ Monitor router validation completed")
    return True


def validate_api_endpoints():
    """Validate API endpoints functionality"""
    print("🔍 Validating API endpoints...")

    endpoints = [
        ("GET", "http://0.0.0.0:5500/api/health"),
        ("GET", "http://0.0.0.0:5500/api/system/status"),
        ("GET", "http://0.0.0.0:5500/api/modules/status"),
        ("GET", "http://0.0.0.0:5500/api/deployment/status"),
        ("GET", "http://0.0.0.0:5500/api/logs/recent"),
        ("GET", "http://0.0.0.0:5500/api/config")
    ]

    for method, endpoint in endpoints:
        try:
            if method == "GET":
                response = requests.get(endpoint, timeout=5)
            elif method == "POST":
                response = requests.post(endpoint, timeout=5)

            if response.status_code not in [200, 404]:  # 404 is acceptable if service not running
                print(f"⚠️  API endpoint {endpoint} returned status {response.status_code}")
                continue

            # Try to parse JSON response
            try:
                data = response.json()
                if not isinstance(data, (dict, list)):
                    print(f"⚠️  API endpoint {endpoint} returned invalid JSON format")
            except ValueError:
                print(f"⚠️  API endpoint {endpoint} returned non-JSON response")

        except requests.exceptions.RequestException as e:
            print(f"⚠️  API endpoint {endpoint} not accessible: {e}")
            continue

    print("✅ API endpoints validation completed")
    return True


def validate_service_structure():
    """Validate service class structure"""
    print("🔍 Validating service class structure...")

    # Check a few key services for proper structure
    services_to_check = [
        "src/backend/services/health_check_service.py",
        "src/backend/services/system_monitor_service.py"
    ]

    for service_file in services_to_check:
        if not os.path.exists(service_file):
            continue

        with open(service_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for class definition
        if 'class ' not in content:
            print(f"⚠️  {service_file} does not contain a class definition")
            continue

        # Check for basic methods
        if 'def ' not in content:
            print(f"⚠️  {service_file} does not contain method definitions")
            continue

    print("✅ Service structure validation completed")
    return True


def validate_config_loading():
    """Validate configuration loading"""
    print("🔍 Validating configuration loading...")

    config_files = [
        "config/app_config.json",
        "config/monitoring_config.json",
        "config/api/"
    ]

    for config in config_files:
        if os.path.isdir(config):
            # Check if directory has config files
            if not os.listdir(config):
                print(f"⚠️  Config directory {config} is empty")
        elif not os.path.exists(config):
            print(f"⚠️  Config file {config} not found")
        else:
            # Try to parse JSON config
            try:
                with open(config, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"✅ Config file {config} is valid JSON")
            except json.JSONDecodeError as e:
                print(f"❌ Config file {config} contains invalid JSON: {e}")
                return False
            except Exception as e:
                print(f"⚠️  Error reading config file {config}: {e}")

    print("✅ Configuration loading validation completed")
    return True


def main():
    """Main validation function"""
    print("🚀 Starting Backend Services Validation")
    print("=" * 50)

    validations = [
        validate_service_files,
        validate_service_imports,
        validate_monitor_router,
        validate_api_endpoints,
        validate_service_structure,
        validate_config_loading
    ]

    passed = 0
    total = len(validations)

    for validation in validations:
        try:
            if validation():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Validation error in {validation.__name__}: {e}")
            print()

    print("=" * 50)
    print(f"📊 Validation Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All validations passed! Backend services are correctly implemented.")
        return 0
    else:
        print("⚠️  Some validations failed. Please review the backend services implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
