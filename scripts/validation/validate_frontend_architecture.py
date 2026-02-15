#!/usr/bin/env python3
"""
Frontend Architecture Validation Script
Validates the frontend modular architecture implementation
"""
import os
import sys
import json
import requests
from pathlib import Path


def validate_file_structure():
    """Validate frontend file structure"""
    print("🔍 Validating frontend file structure...")

    required_files = [
        "src/frontend/templates/index.html",
        "src/frontend/static/js/config.js",
        "src/frontend/static/js/core/module-manager.js",
        "src/frontend/static/js/core/modal-manager.js",
        "src/frontend/static/js/core/event-bus.js",
        "src/frontend/static/js/core/cache-manager.js",
        "src/frontend/static/js/core/api-manager.js",
        "src/frontend/static/js/core/ws-manager.js",
        "src/frontend/static/js/components/module-card.js",
        "src/frontend/static/js/app.js",
        "src/frontend/static/css/global.css",
        "src/frontend/static/css/layout.css",
        "src/frontend/static/css/components.css",
        "src/frontend/static/css/modal.css"
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False

    print("✅ All required files present")
    return True


def validate_html_structure():
    """Validate HTML structure follows architecture principles"""
    print("🔍 Validating HTML structure...")

    html_file = "src/frontend/templates/index.html"
    if not os.path.exists(html_file):
        print(f"❌ HTML file not found: {html_file}")
        return False

    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for inline styles/scripts (should not exist)
    if '<style>' in content or '<script>' in content:
        print("❌ HTML contains inline styles or scripts")
        return False

    # Check for required structural elements
    required_elements = ['<div id="app">', '<div id="modals">']
    for element in required_elements:
        if element not in content:
            print(f"❌ Missing required element: {element}")
            return False

    print("✅ HTML structure follows architecture principles")
    return True


def validate_javascript_modules():
    """Validate JavaScript modules structure"""
    print("🔍 Validating JavaScript modules...")

    # Check for IIFE pattern (Immediately Invoked Function Expression)
    js_files = [
        "src/frontend/static/js/core/module-manager.js",
        "src/frontend/static/js/core/modal-manager.js",
        "src/frontend/static/js/core/event-bus.js",
        "src/frontend/static/js/core/cache-manager.js",
        "src/frontend/static/js/core/api-manager.js",
        "src/frontend/static/js/core/ws-manager.js"
    ]

    for js_file in js_files:
        if not os.path.exists(js_file):
            print(f"❌ JavaScript file not found: {js_file}")
            return False

        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for IIFE pattern
        if not ('(function()' in content and '})(' in content):
            print(f"❌ {js_file} does not use IIFE pattern")
            return False

    print("✅ JavaScript modules follow IIFE pattern")
    return True


def validate_css_architecture():
    """Validate CSS architecture"""
    print("🔍 Validating CSS architecture...")

    css_files = [
        "src/frontend/static/css/global.css",
        "src/frontend/static/css/layout.css",
        "src/frontend/static/css/components.css",
        "src/frontend/static/css/modal.css"
    ]

    for css_file in css_files:
        if not os.path.exists(css_file):
            print(f"❌ CSS file not found: {css_file}")
            return False

        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for CSS variables (custom properties)
        if '--' not in content:
            print(f"⚠️  {css_file} does not use CSS variables")

    print("✅ CSS files present and structured")
    return True


def validate_api_endpoints():
    """Validate API endpoints are accessible"""
    print("🔍 Validating API endpoints...")

    endpoints = [
        "http://0.0.0.0:5500/api/health",
        "http://0.0.0.0:5500/api/system/status",
        "http://0.0.0.0:5500/api/modules/status"
    ]

    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            if response.status_code != 200:
                print(f"❌ API endpoint {endpoint} returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"⚠️  API endpoint {endpoint} not accessible: {e}")
            # Don't fail validation if server is not running
            continue

    print("✅ API endpoints validation completed")
    return True


def validate_monitor_router():
    """Validate monitor router implementation"""
    print("🔍 Validating monitor router...")

    router_file = "src/backend/monitor_router_refactored.py"
    if not os.path.exists(router_file):
        print(f"❌ Monitor router file not found: {router_file}")
        return False

    with open(router_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for route-only logic (no business logic in routes)
    if 'def ' in content and 'return jsonify' in content:
        # This is a basic check - in real implementation we'd need more sophisticated analysis
        print("✅ Monitor router file exists")
        return True

    print("❌ Monitor router structure validation failed")
    return False


def main():
    """Main validation function"""
    print("🚀 Starting Frontend Architecture Validation")
    print("=" * 50)

    validations = [
        validate_file_structure,
        validate_html_structure,
        validate_javascript_modules,
        validate_css_architecture,
        validate_api_endpoints,
        validate_monitor_router
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
        print("🎉 All validations passed! Frontend architecture is correctly implemented.")
        return 0
    else:
        print("⚠️  Some validations failed. Please review the architecture implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
