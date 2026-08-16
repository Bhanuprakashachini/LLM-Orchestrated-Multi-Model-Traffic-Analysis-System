#!/usr/bin/env python
"""
Download YOLO models for the traffic analysis system
"""
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traffic_analysis.settings')

try:
    import django
    django.setup()
    print("✅ Django setup complete")
except ImportError:
    print("Django not available, proceeding without Django setup...")

try:
    from ultralytics import YOLO
    print("✅ Ultralytics available")
except ImportError:
    print("❌ Ultralytics not available. Install with: pip install ultralytics")
    sys.exit(1)

def download_models():
    """Download YOLO models to the models directory"""
    
    # Create models directory
    models_dir = Path(__file__).parent / 'models'
    models_dir.mkdir(exist_ok=True)
    
    # Models to download
    models = [
        ('yolov8s.pt', 'YOLOv8 Small - Balanced performance'),
        ('yolo11s.pt', 'YOLOv11 Small - Enhanced accuracy'),
        ('yolo12s.pt', 'YOLOv12 Small - Latest model, best accuracy'),
    ]
    
    print(f"📁 Models directory: {models_dir}")
    print("🔄 Downloading YOLO models...\n")
    
    for model_name, description in models:
        model_path = models_dir / model_name
        
        # Skip if already exists
        if model_path.exists():
            print(f"✅ {model_name} already exists")
            continue
            
        try:
            print(f"⬇️  Downloading {model_name} ({description})...")
            
            # Load model (this will download it to ultralytics cache)
            model = YOLO(model_name)
            
            # Try to copy from cache to our models directory
            cached_path = model.ckpt_path if hasattr(model, 'ckpt_path') else None
            
            if cached_path and os.path.exists(cached_path):
                # Copy from cache to our models directory
                import shutil
                shutil.copy2(cached_path, model_path)
                print(f"✅ {model_name} downloaded and saved to {model_path}")
            else:
                print(f"✅ {model_name} downloaded to ultralytics cache")
                
        except Exception as e:
            print(f"❌ Failed to download {model_name}: {e}")

if __name__ == "__main__":
    print("🚀 YOLO MODEL DOWNLOADER")
    print("=" * 50)
    
    try:
        download_models()
        
        print("\n" + "=" * 50)
        print("✅ Model download complete!")
        
        # Check device
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"🖥️  Available device: {device}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)