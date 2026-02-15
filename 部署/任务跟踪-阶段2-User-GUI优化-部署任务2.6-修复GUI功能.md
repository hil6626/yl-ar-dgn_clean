# Phase 2 - Task 2.6: Fix GUI Functions - Detailed Deployment Document

**Task ID:** 2.6  
**Task Name:** Fix GUI Functions  
**Priority:** P0 (Blocking)  
**Estimated Hours:** 6 hours  
**Status:** Pending  
**Prerequisites:** Tasks 2.3, 2.4 completed

---

## I. Task Objectives

Fix all GUI functions to ensure video, face synthesis, and audio processing work correctly.

## II. Key Fixes

### 2.1 Video Function Fixes

| Issue | Cause | Solution |
|-------|-------|----------|
| Camera won't start | Permission/Driver | Check permissions, use virtual camera fallback |
| Frame processing error | Thread safety | Add locks, exception handling |
| Memory leak | Unreleased resources | Use context managers, periodic cleanup |

### 2.2 Face Synthesis Fixes

| Issue | Cause | Solution |
|-------|-------|----------|
| Model loading failure | Path/Dependency | Verify paths, check model integrity |
| Out of memory | Large models | Progressive loading, memory optimization |
| Synthesis failure | API mismatch | Version detection, compatibility layer |

### 2.3 Audio Processing Fixes

| Issue | Cause | Solution |
|-------|-------|----------|
| Device occupied | Exclusive mode | Check device status, use software processing |
| Processing delay | Buffer settings | Adjust buffer size, use low-latency mode |
| Effect not working | Parameter error | Validate parameters, use default values |

## III. Core Code Fixes

### Fix 1: Video Thread Safety

```python
# Add in gui.py VideoWorker
import threading

class VideoWorker(QThread):
    def __init__(self, camera_module):
        super().__init__()
        self.camera_module = camera_module
        self.running = False
        self._lock = threading.Lock()  # Add lock
    
    def run(self):
        self.running = True
        while self.running:
            try:
                with self._lock:  # Use lock
                    if self.camera_module and self.camera_module.capture:
                        ret, frame = self.camera_module.capture.read()
                        if ret:
                            self.frame_ready.emit(frame)
                self.msleep(33)
            except Exception as e:
                self.error_occurred.emit(str(e))
                self.msleep(100)
```

### Fix 2: Resource Management

```python
# Add resource cleanup
def cleanup_resources(self):
    """Clean up resources"""
    # Stop video
    if self.video_worker:
        self.video_worker.stop()
        self.video_worker = None
    
    # Stop camera
    if self.camera_module:
        self.camera_module.stop()
        self.camera_module = None
    
    # Stop audio
    if self.audio_module:
        self.audio_module.stop()
        self.audio_module = None
    
    # Force garbage collection
    import gc
    gc.collect()
```

### Fix 3: Exception Handling

```python
# Add global exception handling
def safe_call(func, *args, **kwargs):
    """Safe function call"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logging.error(f"Error in {func.__name__}: {e}")
        return None
```

## IV. Deployment Steps

```bash
# 1. Backup original files
cp user/gui/gui.py user/gui/gui.py.backup

# 2. Apply fixes
# Modify user/gui/gui.py

# 3. Test functions
cd user
python3 -c "
from gui.gui import ARApp
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = ARApp()
print('GUI created successfully')
# Test camera start
# window.toggle_camera(True)
"

# 4. Memory leak test
python3 -c "
import psutil
import time

process = psutil.Process()
initial_memory = process.memory_info().rss

# Run GUI for 5 minutes
# ...

final_memory = process.memory_info().rss
print(f'Memory change: {(final_memory - initial_memory) / 1024 / 1024:.2f} MB')
"
```

## V. Verification Checklist

- [ ] Camera starts normally
- [ ] Video displays without lag
- [ ] Face synthesis works
- [ ] Audio processing normal
- [ ] No memory leaks
- [ ] No interface lag
- [ ] Exception handling effective

## VI. Next Step

After completing this task, proceed to **Task 2.7: Add Startup Script**

View document: `部署/任务跟踪-阶段2-User-GUI优化-部署任务2.7-添加启动脚本.md`
