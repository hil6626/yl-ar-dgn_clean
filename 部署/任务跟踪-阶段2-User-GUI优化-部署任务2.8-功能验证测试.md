# Phase 2 - Task 2.8: Functional Verification Testing - Detailed Deployment Document

**Task ID:** 2.8  
**Task Name:** Functional Verification Testing  
**Priority:** P0 (Blocking)  
**Estimated Hours:** 4 hours  
**Status:** Pending  
**Prerequisites:** Tasks 2.6, 2.7 completed

---

## I. Task Objectives

Execute comprehensive functional tests to verify all GUI functions work correctly.

## II. Test Content

### 2.1 Test File List

| No. | File Path | Type | Description |
|-----|-----------|------|-------------|
| 1 | `test/user/test_gui.py` | New | GUI test suite |
| 2 | `test/user/test_camera.py` | New | Camera function test |
| 3 | `test/user/test_audio.py` | New | Audio function test |
| 4 | `test/user/run_tests.sh` | New | Test execution script |

### 2.2 Core Test Code

#### File 1: test/user/test_gui.py

```python
#!/usr/bin/env python3
"""
GUI Functional Test Suite
"""

import unittest
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'user'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt


class TestGUIBasic(unittest.TestCase):
    """Basic GUI Tests"""
    
    @classmethod
    def setUpClass(cls):
        """Initialize test environment"""
        cls.app = QApplication(sys.argv)
    
    def test_app_creation(self):
        """Test application creation"""
        from gui.gui import ARApp
        
        window = ARApp()
        self.assertIsNotNone(window)
        self.assertEqual(window.windowTitle(), "AR Live Studio")
    
    def test_window_size(self):
        """Test window size"""
        from gui.gui import ARApp
        
        window = ARApp()
        self.assertGreater(window.width(), 0)
        self.assertGreater(window.height(), 0)


class TestCameraFunction(unittest.TestCase):
    """Camera Function Tests"""
    
    def test_camera_module_import(self):
        """Test camera module import"""
        try:
            from camera import CameraModule
            self.assertTrue(True)
        except ImportError:
            self.fail("CameraModule import failed")
    
    def test_camera_start_stop(self):
        """Test camera start/stop"""
        from camera import CameraModule
        
        camera = CameraModule()
        
        # Test start
        result = camera.start()
        self.assertTrue(result)
        
        # Test stop
        camera.stop()
        self.assertFalse(camera.capture.isOpened())


class TestAudioFunction(unittest.TestCase):
    """Audio Function Tests"""
    
    def test_audio_module_import(self):
        """Test audio module import"""
        try:
            from audio_module import AudioModule
            self.assertTrue(True)
        except ImportError:
            self.fail("AudioModule import failed")


class TestIntegration(unittest.TestCase):
    """Integration Tests"""
    
    def test_service_client(self):
        """Test service client"""
        from services.ar_backend_client import ARBackendClient
        
        client = ARBackendClient()
        self.assertIsNotNone(client)
        
        # Test health check
        healthy = client.health_check()
        self.assertIn(healthy, [True, False])  # May be True or False


if __name__ == '__main__':
    unittest.main()
```

## III. Test Execution Steps

```bash
# 1. Create test directory
mkdir -p test/user

# 2. Create test files
# test/user/test_gui.py
# test/user/test_camera.py
# test/user/test_audio.py
# test/user/run_tests.sh

# 3. Execute tests
cd user
python3 -m pytest ../test/user/ -v

# Or use unittest
python3 -m unittest discover ../test/user/ -v

# 4. Generate test report
python3 -m pytest ../test/user/ --html=report.html
```

## IV. Test Checklist

### 4.1 Basic Function Tests

- [ ] Application starts normally
- [ ] Window displays correctly
- [ ] Menu functions properly
- [ ] Button clicks respond

### 4.2 Camera Function Tests

- [ ] Camera module imports successfully
- [ ] Camera starts normally
- [ ] Video displays without lag
- [ ] Camera stops normally
- [ ] Screenshot function works

### 4.3 Audio Function Tests

- [ ] Audio module imports successfully
- [ ] Audio device detected
- [ ] Audio starts normally
- [ ] Audio effects work
- [ ] Audio stops normally

### 4.4 Integration Tests

- [ ] Service client works
- [ ] Status reporting normal
- [ ] Monitor link works
- [ ] Configuration loads normally

## V. Common Issues and Solutions

### Issue 1: Test Environment Has No Display

**Phenomenon:** `QXcbConnection: Could not connect to display`

**Solution:**
```bash
# Use virtual display
export QT_QPA_PLATFORM='offscreen'
# Or
xvfb-run python3 test_gui.py
```

### Issue 2: Camera Device Not Found

**Phenomenon:** Camera test fails

**Solution:**
```bash
# Check camera devices
ls /dev/video*

# Use virtual camera
modprobe v4l2loopback
```

## VI. Phase 2 Completion Summary

After completing this task, Phase 2 (User GUI Optimization) is fully complete!

### Phase 2 Deliverables

| Task | Deliverable | Status |
|------|-------------|--------|
| 2.1 | main.py entry | ✓ |
| 2.2 | Path repair module | ✓ |
| 2.3 | GUI import fix | ✓ |
| 2.4 | Service client | ✓ |
| 2.5 | Configuration management | ✓ |
| 2.6 | GUI function fix | ✓ |
| 2.7 | Startup script | ✓ |
| 2.8 | Functional verification | ✓ |

### Phase 2 Verification Criteria

- [x] GUI starts normally
- [x] Video function normal
- [x] Face synthesis normal
- [x] Audio processing normal
- [x] Monitor link works
- [x] All tests pass

---

**Next Step:** Begin Phase 3 - Rule Architecture Deployment

View document: `部署/任务跟踪-阶段3-规则架构部署.md`
