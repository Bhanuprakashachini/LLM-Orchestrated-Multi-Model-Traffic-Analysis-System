"""
Custom Training Service for Fine-tuning YOLO models on local traffic data
"""
import os
import json
import yaml
from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)


class CustomTrainingService:
    """
    Service for fine-tuning YOLO models on custom traffic datasets
    """
    
    def __init__(self, base_model: str = None):
        """
        Initialize custom training service
        """
        if base_model is None:
            base_model = os.path.join('backend', 'models', 'yolov8s.pt')
        
        Args:
            base_model: Base YOLO model to fine-tune
        """
        self.base_model = base_model
        self.training_dir = Path(__file__).parent.parent.parent / 'custom_training'
        self.datasets_dir = self.training_dir / 'datasets'
        self.models_dir = self.training_dir / 'models'
        self.results_dir = self.training_dir / 'results'
        
        # Create directories
        for dir_path in [self.training_dir, self.datasets_dir, self.models_dir, self.results_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Vehicle classes for traffic analysis
        self.traffic_classes = [
            'car', 'motorcycle', 'bus', 'truck', 'bicycle', 
            'person', 'traffic_light', 'stop_sign'
        ]
    
    def prepare_dataset(self, images_dir: str, annotations_dir: str, 
                       dataset_name: str = None) -> Dict[str, Any]:
        """
        Prepare dataset for YOLO training
        
        Args:
            images_dir: Directory containing training images
            annotations_dir: Directory containing YOLO format annotations
            dataset_name: Name for the dataset
            
        Returns:
            Dictionary with dataset preparation results
        """
        if dataset_name is None:
            dataset_name = f"traffic_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        dataset_path = self.datasets_dir / dataset_name
        dataset_path.mkdir(exist_ok=True)
        
        try:
            # Create dataset structure
            train_images_dir = dataset_path / 'images' / 'train'
            val_images_dir = dataset_path / 'images' / 'val'
            train_labels_dir = dataset_path / 'labels' / 'train'
            val_labels_dir = dataset_path / 'labels' / 'val'
            
            for dir_path in [train_images_dir, val_images_dir, train_labels_dir, val_labels_dir]:
                dir_path.mkdir(parents=True, exist_ok=True)
            
            # Copy and split images/annotations (80% train, 20% val)
            image_files = list(Path(images_dir).glob('*.jpg')) + list(Path(images_dir).glob('*.png'))
            total_images = len(image_files)
            
            if total_images == 0:
                raise ValueError(f"No images found in {images_dir}")
            
            train_split = int(total_images * 0.8)
            
            train_images = image_files[:train_split]
            val_images = image_files[train_split:]
            
            # Copy training images and labels
            for img_path in train_images:
                # Copy image
                shutil.copy2(img_path, train_images_dir / img_path.name)
                
                # Copy corresponding label
                label_path = Path(annotations_dir) / f"{img_path.stem}.txt"
                if label_path.exists():
                    shutil.copy2(label_path, train_labels_dir / label_path.name)
            
            # Copy validation images and labels
            for img_path in val_images:
                # Copy image
                shutil.copy2(img_path, val_images_dir / img_path.name)
                
                # Copy corresponding label
                label_path = Path(annotations_dir) / f"{img_path.stem}.txt"
                if label_path.exists():
                    shutil.copy2(label_path, val_labels_dir / label_path.name)
            
            # Create dataset YAML file
            dataset_yaml = {
                'path': str(dataset_path),
                'train': 'images/train',
                'val': 'images/val',
                'nc': len(self.traffic_classes),
                'names': self.traffic_classes
            }
            
            yaml_path = dataset_path / 'dataset.yaml'
            with open(yaml_path, 'w') as f:
                yaml.dump(dataset_yaml, f, default_flow_style=False)
            
            logger.info(f"Dataset prepared: {total_images} images ({len(train_images)} train, {len(val_images)} val)")
            
            return {
                'dataset_name': dataset_name,
                'dataset_path': str(dataset_path),
                'yaml_path': str(yaml_path),
                'total_images': total_images,
                'train_images': len(train_images),
                'val_images': len(val_images),
                'classes': self.traffic_classes,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Dataset preparation failed: {e}")
            return {
                'dataset_name': dataset_name,
                'error': str(e),
                'status': 'failed'
            }
    
    def start_training(self, dataset_yaml_path: str, epochs: int = 100, 
                      batch_size: int = 16, img_size: int = 640,
                      device: str = 'auto') -> Dict[str, Any]:
        """
        Start custom training
        
        Args:
            dataset_yaml_path: Path to dataset YAML file
            epochs: Number of training epochs
            batch_size: Training batch size
            img_size: Input image size
            device: Device to use for training
            
        Returns:
            Dictionary with training results
        """
        try:
            from ultralytics import YOLO
            
            # Load base model
            model = YOLO(self.base_model)
            
            # Create unique training run name
            run_name = f"traffic_training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Training parameters
            training_args = {
                'data': dataset_yaml_path,
                'epochs': epochs,
                'batch': batch_size,
                'imgsz': img_size,
                'device': device,
                'project': str(self.results_dir),
                'name': run_name,
                'save': True,
                'save_period': 10,  # Save every 10 epochs
                'patience': 20,     # Early stopping patience
                'optimizer': 'AdamW',
                'lr0': 0.01,        # Initial learning rate
                'weight_decay': 0.0005,
                'warmup_epochs': 3,
                'box': 7.5,         # Box loss gain
                'cls': 0.5,         # Class loss gain
                'dfl': 1.5,         # DFL loss gain
                'augment': True,    # Use augmentation
                'mosaic': 1.0,      # Mosaic augmentation probability
                'mixup': 0.1,       # MixUp augmentation probability
                'copy_paste': 0.1,  # Copy-paste augmentation probability
                'degrees': 10.0,    # Rotation degrees
                'translate': 0.1,   # Translation fraction
                'scale': 0.5,       # Scaling factor
                'shear': 2.0,       # Shear degrees
                'perspective': 0.0, # Perspective transformation
                'flipud': 0.0,      # Vertical flip probability
                'fliplr': 0.5,      # Horizontal flip probability
                'hsv_h': 0.015,     # HSV hue augmentation
                'hsv_s': 0.7,       # HSV saturation augmentation
                'hsv_v': 0.4        # HSV value augmentation
            }
            
            logger.info(f"Starting training with {epochs} epochs, batch size {batch_size}")
            
            # Start training
            results = model.train(**training_args)
            
            # Get best model path
            best_model_path = self.results_dir / run_name / 'weights' / 'best.pt'
            
            # Save training configuration
            config_path = self.results_dir / run_name / 'training_config.json'
            with open(config_path, 'w') as f:
                json.dump({
                    'base_model': self.base_model,
                    'dataset_yaml': dataset_yaml_path,
                    'training_args': training_args,
                    'run_name': run_name,
                    'timestamp': datetime.now().isoformat()
                }, f, indent=2)
            
            logger.info(f"Training completed. Best model saved to: {best_model_path}")
            
            return {
                'run_name': run_name,
                'best_model_path': str(best_model_path),
                'results_dir': str(self.results_dir / run_name),
                'config_path': str(config_path),
                'training_args': training_args,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def evaluate_model(self, model_path: str, dataset_yaml_path: str) -> Dict[str, Any]:
        """
        Evaluate trained model
        
        Args:
            model_path: Path to trained model
            dataset_yaml_path: Path to dataset YAML file
            
        Returns:
            Dictionary with evaluation results
        """
        try:
            from ultralytics import YOLO
            
            # Load trained model
            model = YOLO(model_path)
            
            # Run validation
            results = model.val(data=dataset_yaml_path, save_json=True, save_hybrid=True)
            
            # Extract metrics
            metrics = {
                'map50': results.box.map50,      # mAP@0.5
                'map50_95': results.box.map,     # mAP@0.5:0.95
                'precision': results.box.mp,     # Mean precision
                'recall': results.box.mr,        # Mean recall
                'f1_score': 2 * (results.box.mp * results.box.mr) / (results.box.mp + results.box.mr) if (results.box.mp + results.box.mr) > 0 else 0
            }
            
            # Per-class metrics
            class_metrics = {}
            if hasattr(results.box, 'ap_class_index') and hasattr(results.box, 'ap'):
                for i, class_idx in enumerate(results.box.ap_class_index):
                    if class_idx < len(self.traffic_classes):
                        class_name = self.traffic_classes[class_idx]
                        class_metrics[class_name] = {
                            'ap50': results.box.ap50[i],
                            'ap50_95': results.box.ap[i]
                        }
            
            logger.info(f"Model evaluation completed. mAP@0.5: {metrics['map50']:.3f}")
            
            return {
                'model_path': model_path,
                'overall_metrics': metrics,
                'class_metrics': class_metrics,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Model evaluation failed: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def create_annotation_template(self, images_dir: str, output_dir: str) -> Dict[str, Any]:
        """
        Create annotation template files for manual labeling
        
        Args:
            images_dir: Directory containing images to annotate
            output_dir: Directory to save annotation templates
            
        Returns:
            Dictionary with template creation results
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # Get all image files
            image_files = list(Path(images_dir).glob('*.jpg')) + list(Path(images_dir).glob('*.png'))
            
            # Create empty annotation files
            created_files = []
            for img_path in image_files:
                annotation_path = output_path / f"{img_path.stem}.txt"
                
                # Create empty annotation file with header comment
                with open(annotation_path, 'w') as f:
                    f.write("# YOLO format annotations\n")
                    f.write("# Format: class_id center_x center_y width height\n")
                    f.write("# Coordinates are normalized (0-1)\n")
                    f.write("# Classes:\n")
                    for i, class_name in enumerate(self.traffic_classes):
                        f.write(f"# {i}: {class_name}\n")
                    f.write("\n")
                
                created_files.append(str(annotation_path))
            
            # Create classes reference file
            classes_file = output_path / 'classes.txt'
            with open(classes_file, 'w') as f:
                for i, class_name in enumerate(self.traffic_classes):
                    f.write(f"{i}: {class_name}\n")
            
            logger.info(f"Created {len(created_files)} annotation templates")
            
            return {
                'output_dir': str(output_path),
                'annotation_files': created_files,
                'classes_file': str(classes_file),
                'total_files': len(created_files),
                'classes': self.traffic_classes,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Template creation failed: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def get_training_status(self, run_name: str) -> Dict[str, Any]:
        """
        Get status of a training run
        
        Args:
            run_name: Name of the training run
            
        Returns:
            Dictionary with training status
        """
        try:
            run_dir = self.results_dir / run_name
            
            if not run_dir.exists():
                return {'error': f'Training run {run_name} not found', 'status': 'not_found'}
            
            # Check for results files
            weights_dir = run_dir / 'weights'
            best_model = weights_dir / 'best.pt'
            last_model = weights_dir / 'last.pt'
            
            # Check for training logs
            results_csv = run_dir / 'results.csv'
            
            status_info = {
                'run_name': run_name,
                'run_dir': str(run_dir),
                'best_model_exists': best_model.exists(),
                'last_model_exists': last_model.exists(),
                'results_csv_exists': results_csv.exists(),
                'status': 'unknown'
            }
            
            if best_model.exists():
                status_info['status'] = 'completed'
                status_info['best_model_path'] = str(best_model)
            elif last_model.exists():
                status_info['status'] = 'in_progress'
                status_info['last_model_path'] = str(last_model)
            else:
                status_info['status'] = 'failed_or_not_started'
            
            # Read training results if available
            if results_csv.exists():
                try:
                    import pandas as pd
                    df = pd.read_csv(results_csv)
                    
                    if not df.empty:
                        latest_metrics = df.iloc[-1].to_dict()
                        status_info['latest_metrics'] = {
                            k: v for k, v in latest_metrics.items() 
                            if not pd.isna(v)
                        }
                        status_info['total_epochs'] = len(df)
                        
                except Exception as e:
                    logger.warning(f"Could not read results CSV: {e}")
            
            return status_info
            
        except Exception as e:
            logger.error(f"Failed to get training status: {e}")
            return {
                'error': str(e),
                'status': 'error'
            }
    
    def list_available_models(self) -> Dict[str, Any]:
        """
        List all available trained models
        
        Returns:
            Dictionary with available models
        """
        try:
            models = []
            
            # Scan results directory for trained models
            if self.results_dir.exists():
                for run_dir in self.results_dir.iterdir():
                    if run_dir.is_dir():
                        weights_dir = run_dir / 'weights'
                        best_model = weights_dir / 'best.pt'
                        
                        if best_model.exists():
                            # Try to read config
                            config_path = run_dir / 'training_config.json'
                            config = {}
                            if config_path.exists():
                                try:
                                    with open(config_path, 'r') as f:
                                        config = json.load(f)
                                except Exception:
                                    pass
                            
                            models.append({
                                'run_name': run_dir.name,
                                'model_path': str(best_model),
                                'config': config,
                                'created': datetime.fromtimestamp(best_model.stat().st_mtime).isoformat()
                            })
            
            return {
                'available_models': models,
                'total_models': len(models),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return {
                'error': str(e),
                'status': 'failed'
            }