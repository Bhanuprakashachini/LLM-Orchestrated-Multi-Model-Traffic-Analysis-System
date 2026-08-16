# YOLO Models Directory

This directory should contain the PyTorch YOLO model files for server-side inference.

## Required Models

### YOLOv8 Models (Current)
- `yolov8n.pt` - Nano model (6.2 MB) - Fast inference
- `yolov8s.pt` - Small model (21.5 MB) - Balanced performance
- `yolov8m.pt` - Medium model (49.7 MB) - Better accuracy
- `yolov8l.pt` - Large model (83.7 MB) - High accuracy
- `yolov8x.pt` - Extra Large model (136 MB) - Highest accuracy

### YOLOv12 Models (Future)
- `yolov12n.pt` - When available
- `yolov12s.pt` - When available

## Download Instructions

### Option 1: Automatic Download (Recommended)
The models will be automatically downloaded by Ultralytics when first used:

```python
from ultralytics import YOLO
model = YOLO('yolov8s.pt')  # Downloads automatically if not present
```

### Option 2: Manual Download
```bash
# Create models directory
mkdir -p backend/models

# Download YOLOv8 models
wget -O backend/models/yolov8n.pt https://github.com/ultralytics/assets/releases/download/v8.0.0/yolov8n.pt
wget -O backend/models/yolov8s.pt https://github.com/ultralytics/assets/releases/download/v8.0.0/yolov8s.pt
wget -O backend/models/yolov8m.pt https://github.com/ultralytics/assets/releases/download/v8.0.0/yolov8m.pt
```

### Option 3: Python Script
```python
from ultralytics import YOLO
import os

# Ensure models directory exists
os.makedirs('backend/models', exist_ok=True)

# Download and save models
models = ['yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt']
for model_name in models:
    model = YOLO(model_name)
    # Model is now cached in ~/.ultralytics/
    print(f"✅ {model_name} ready")
```

## Configuration

Update your Django settings to point to the models directory:

```python
# backend/traffic_analysis/settings.py
YOLO_MODEL_PATH = os.path.join(BASE_DIR, 'models', 'yolov8s.pt')
YOLO_DEVICE = config('YOLO_DEVICE', default='cpu')  # or 'cuda:0' for GPU
```

## Model Selection Strategy

The system should use models in this priority order:

1. **YOLOv12** (when available) - Latest and most accurate
2. **YOLOv8s** - Default balanced model
3. **YOLOv8n** - Fallback for speed
4. **Auto-download** - If no local models found

## Storage Locations

### Local Development
- `backend/models/` - Project-specific models
- `~/.ultralytics/` - Ultralytics cache directory

### Production
- Mount persistent volume for models
- Use environment variables for model paths
- Consider model registry for version control

## Performance Notes

- **GPU**: Use CUDA-enabled models for better performance
- **CPU**: YOLOv8n recommended for CPU-only environments
- **Memory**: Larger models require more RAM
- **Speed**: Nano < Small < Medium < Large < Extra Large

## Troubleshooting

### Common Issues
1. **Model not found**: Check file paths and permissions
2. **CUDA errors**: Ensure GPU drivers and PyTorch CUDA support
3. **Memory errors**: Use smaller models or reduce batch size
4. **Download failures**: Check internet connection and firewall

### Verification
```python
from ultralytics import YOLO
import torch

# Check available models
model = YOLO('yolov8s.pt')
print(f"Model loaded: {model.model}")
print(f"Device: {next(model.model.parameters()).device}")
print(f"CUDA available: {torch.cuda.is_available()}")
```