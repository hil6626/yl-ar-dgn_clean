# Backend Tests Directory

This directory contains unit and integration tests for backend components.

## Purpose
- Test backend logic and integrations
- Validate API endpoints and services
- Ensure backend modules work correctly

## Test Files
- `test_camera.py` - Test camera capture and processing
- `test_face_modules.py` - Test face synthesis modules
- `test_audio_modules.py` - Test audio processing
- `test_api.py` - Test REST API endpoints

## Running Tests
```bash
cd test/test_backend
python -m pytest
```

## Coverage
Aim for >80% code coverage.

## Notes
- Tests use mock objects for external dependencies
- Integration tests require running services
- Results integrated with CI/CD pipeline
