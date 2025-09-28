#!/usr/bin/env python3
"""
ONNX Model Conversion Utility for BlockMarket Trading Agents

This module provides functionality to convert PyTorch models (.pth files) to ONNX format
for NPU utilization on Qualcomm Snapdragon X Elite devices. This enables the trading
agent neural networks to leverage 45 TOPS of AI performance for real-time inference.

Key Features:
- Automatic discovery of .pth model files
- Conversion to ONNX format with NPU optimization hints
- Validation of converted models
- Batch processing capabilities
- Integration with existing TradingAgent architecture
"""

import os
import glob
import logging
import torch
import torch.onnx
import numpy as np
import onnx
import onnxruntime as ort
from typing import List, Dict, Tuple, Optional, Union
from pathlib import Path
import json
import yaml

try:
    from .network import TradingNetwork, ValueNetwork, ActorCriticNetwork
    from .agent import TradingAgent
    from .config import load_config
except ImportError:
    from network import TradingNetwork, ValueNetwork, ActorCriticNetwork
    from agent import TradingAgent
    from config import load_config


logger = logging.getLogger(__name__)


class ONNXConverter:
    """
    Handles conversion of PyTorch trading models to ONNX format for NPU acceleration.
    
    This converter is designed specifically for BlockMarket trading agent models,
    handling the unique architecture and state requirements of trading networks.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the ONNX converter.
        
        Args:
            config: Configuration dictionary (loaded from config.yaml if not provided)
        """
        self.config = config or load_config()
        self.model_save_path = self.config['training']['model_save_path']
        self.items_list = self.config['environment']['items_list']
        self.num_items = len(self.items_list)
        
        # Create output directory for ONNX models
        self.onnx_output_dir = os.path.join(self.model_save_path, 'onnx')
        os.makedirs(self.onnx_output_dir, exist_ok=True)
        
        logger.info(f"ONNX Converter initialized")
        logger.info(f"Model path: {self.model_save_path}")
        logger.info(f"ONNX output: {self.onnx_output_dir}")
        logger.info(f"Items: {self.items_list}")
    
    def discover_pth_files(self, pattern: str = "*.pth") -> List[str]:
        """
        Discover all .pth model files in the model directory.
        
        Args:
            pattern: Glob pattern to match files (default: "*.pth")
            
        Returns:
            List of paths to .pth files
        """
        search_pattern = os.path.join(self.model_save_path, pattern)
        pth_files = glob.glob(search_pattern, recursive=True)
        
        # Also search subdirectories
        recursive_pattern = os.path.join(self.model_save_path, "**", pattern)
        pth_files.extend(glob.glob(recursive_pattern, recursive=True))
        
        # Remove duplicates and sort
        pth_files = sorted(list(set(pth_files)))
        
        logger.info(f"Found {len(pth_files)} .pth files:")
        for file in pth_files:
            logger.info(f"  - {file}")
        
        return pth_files
    
    def load_pytorch_model(self, pth_path: str) -> Tuple[TradingNetwork, Dict]:
        """
        Load a PyTorch model from a .pth file.
        
        Args:
            pth_path: Path to the .pth file
            
        Returns:
            Tuple of (model, checkpoint_data)
        """
        try:
            logger.info(f"Loading PyTorch model from: {pth_path}")
            
            # Load checkpoint
            checkpoint = torch.load(pth_path, map_location='cpu', weights_only=False)
            
            # Create network with proper configuration
            network = TradingNetwork(self.config, self.num_items)
            
            # Load state dict
            network.load_state_dict(checkpoint['network_state_dict'])
            network.eval()  # Set to evaluation mode
            
            logger.info(f"Successfully loaded model: {pth_path}")
            return network, checkpoint
            
        except Exception as e:
            logger.error(f"Failed to load PyTorch model from {pth_path}: {e}")
            raise
    
    def create_dummy_input(self) -> torch.Tensor:
        """
        Create dummy input tensor for ONNX export.
        
        This creates a properly shaped input tensor that matches the expected
        input format for TradingNetwork models.
        
        Returns:
            Dummy input tensor
        """
        # Calculate input dimension as defined in TradingNetwork.__init__
        # inventory (num_items) + desired_item_one_hot (num_items) + 
        # current_trading_matrix (num_items^2) + market_rates (num_items^2) + 
        # success_rate (1)
        input_dim = (
            self.num_items +  # inventory
            self.num_items +  # desired item one-hot
            (self.num_items * self.num_items) +  # current trading matrix
            (self.num_items * self.num_items) +  # market rates
            1  # success rate
        )
        
        # Create random dummy input
        dummy_input = torch.randn(1, input_dim, dtype=torch.float32)
        
        logger.debug(f"Created dummy input with shape: {dummy_input.shape}")
        return dummy_input
    
    def convert_to_onnx(
        self,
        model: TradingNetwork,
        onnx_path: str,
        dummy_input: Optional[torch.Tensor] = None,
        opset_version: int = 11
    ) -> bool:
        """
        Convert PyTorch model to ONNX format.
        
        Args:
            model: PyTorch TradingNetwork model
            onnx_path: Output path for ONNX model
            dummy_input: Input tensor for tracing (created automatically if None)
            opset_version: ONNX opset version
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            if dummy_input is None:
                dummy_input = self.create_dummy_input()
            
            logger.info(f"Converting to ONNX: {onnx_path}")
            
            # Export to ONNX
            torch.onnx.export(
                model,
                dummy_input,
                onnx_path,
                export_params=True,
                opset_version=opset_version,
                do_constant_folding=True,
                input_names=['state_vector'],
                output_names=['trading_matrix'],
                dynamic_axes={
                    'state_vector': {0: 'batch_size'},
                    'trading_matrix': {0: 'batch_size'}
                },
                verbose=False
            )
            
            logger.info(f"ONNX export completed: {onnx_path}")
            return True
            
        except Exception as e:
            logger.error(f"ONNX conversion failed: {e}")
            return False
    
    def validate_onnx_model(
        self,
        onnx_path: str,
        pytorch_model: TradingNetwork,
        tolerance: float = 1e-5
    ) -> bool:
        """
        Validate ONNX model by comparing outputs with PyTorch model.
        
        Args:
            onnx_path: Path to ONNX model
            pytorch_model: Original PyTorch model
            tolerance: Numerical tolerance for comparison
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            logger.info(f"Validating ONNX model: {onnx_path}")
            
            # Load ONNX model
            onnx_model = onnx.load(onnx_path)
            onnx.checker.check_model(onnx_model)
            
            # Create ONNX Runtime session
            ort_session = ort.InferenceSession(onnx_path)
            
            # Create test input
            test_input = self.create_dummy_input()
            
            # Get PyTorch output
            pytorch_model.eval()
            with torch.no_grad():
                pytorch_output = pytorch_model(test_input)
            
            # Get ONNX output
            onnx_output = ort_session.run(
                None,
                {'state_vector': test_input.numpy()}
            )[0]
            
            # Compare outputs
            pytorch_np = pytorch_output.detach().numpy()
            max_diff = np.max(np.abs(pytorch_np - onnx_output))
            
            if max_diff < tolerance:
                logger.info(f"ONNX validation PASSED (max_diff: {max_diff:.2e})")
                return True
            else:
                logger.warning(f"ONNX validation FAILED (max_diff: {max_diff:.2e})")
                return False
                
        except Exception as e:
            logger.error(f"ONNX validation failed: {e}")
            return False
    
    def create_npu_optimized_metadata(
        self,
        onnx_path: str,
        checkpoint_data: Dict,
        validation_passed: bool
    ) -> Dict:
        """
        Create metadata file for NPU-optimized model.
        
        Args:
            onnx_path: Path to ONNX model
            checkpoint_data: Original checkpoint data from .pth file
            validation_passed: Whether validation passed
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "model_info": {
                "onnx_path": os.path.basename(onnx_path),
                "model_type": "TradingNetwork",
                "input_dim": self.num_items * 2 + (self.num_items * self.num_items) * 2 + 1,
                "output_dim": self.num_items * self.num_items,
                "items_list": self.items_list,
                "num_items": self.num_items,
                "validation_passed": validation_passed
            },
            "agent_info": {
                "agent_id": checkpoint_data.get('agent_id', 'unknown'),
                "desired_item": checkpoint_data.get('desired_item', 'unknown'),
                "training_history": len(checkpoint_data.get('reward_history', []))
            },
            "npu_optimization": {
                "target_device": "Qualcomm Snapdragon X Elite",
                "expected_tops": 45,
                "optimization_hints": [
                    "Use QNN backend for inference",
                    "Enable NPU execution provider",
                    "Consider FP16 quantization for better performance",
                    "Batch size = 1 recommended for real-time inference"
                ]
            },
            "conversion_info": {
                "opset_version": 11,
                "torch_version": torch.__version__,
                "onnx_version": onnx.__version__
            }
        }
        
        return metadata
    
    def save_metadata(self, metadata: Dict, metadata_path: str) -> None:
        """
        Save metadata to JSON file.
        
        Args:
            metadata: Metadata dictionary
            metadata_path: Output path for metadata file
        """
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Metadata saved: {metadata_path}")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def convert_single_model(self, pth_path: str) -> bool:
        """
        Convert a single .pth model to ONNX format.
        
        Args:
            pth_path: Path to .pth file
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # Load PyTorch model
            pytorch_model, checkpoint_data = self.load_pytorch_model(pth_path)
            
            # Generate ONNX output path
            pth_filename = os.path.basename(pth_path)
            onnx_filename = pth_filename.replace('.pth', '.onnx')
            onnx_path = os.path.join(self.onnx_output_dir, onnx_filename)
            
            # Convert to ONNX
            conversion_success = self.convert_to_onnx(pytorch_model, onnx_path)
            if not conversion_success:
                return False
            
            # Validate ONNX model
            validation_passed = self.validate_onnx_model(onnx_path, pytorch_model)
            
            # Create and save metadata
            metadata = self.create_npu_optimized_metadata(
                onnx_path, checkpoint_data, validation_passed
            )
            metadata_path = onnx_path.replace('.onnx', '_metadata.json')
            self.save_metadata(metadata, metadata_path)
            
            logger.info(f"✅ Successfully converted: {pth_filename} -> {onnx_filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to convert {pth_path}: {e}")
            return False
    
    def convert_all_models(self, pattern: str = "*.pth") -> Dict[str, bool]:
        """
        Convert all .pth models found in the model directory.
        
        Args:
            pattern: Glob pattern to match files
            
        Returns:
            Dictionary mapping file paths to conversion success status
        """
        logger.info("Starting batch conversion of all models...")
        
        pth_files = self.discover_pth_files(pattern)
        if not pth_files:
            logger.warning("No .pth files found for conversion")
            return {}
        
        results = {}
        successful_conversions = 0
        
        for pth_path in pth_files:
            success = self.convert_single_model(pth_path)
            results[pth_path] = success
            if success:
                successful_conversions += 1
        
        logger.info("="*60)
        logger.info("🏁 BATCH CONVERSION COMPLETED")
        logger.info(f"Successful: {successful_conversions}/{len(pth_files)}")
        logger.info(f"ONNX models saved to: {self.onnx_output_dir}")
        logger.info("="*60)
        
        return results
    
    def create_npu_inference_example(self) -> str:
        """
        Create example code for using ONNX models with NPU acceleration.
        
        Returns:
            Python code string showing how to use converted models
        """
        example_code = '''
"""
Example: Using ONNX Trading Models with NPU Acceleration
"""
import onnxruntime as ort
import numpy as np
import json

# Configure ONNX Runtime for NPU acceleration
def create_npu_session(onnx_path: str):
    """Create ONNX Runtime session optimized for Qualcomm NPU."""
    
    # Set up execution providers for Snapdragon X Elite NPU
    providers = [
        ('QNNExecutionProvider', {
            'backend_path': 'QnnHtp.dll',  # Qualcomm NPU backend
            'profiling_level': 'basic',
            'rpc_control_latency': 1000,
            'vtcm_mb': 8,
            'htp_performance_mode': 'burst'
        }),
        'CPUExecutionProvider'  # Fallback
    ]
    
    # Create session with NPU optimization
    session_options = ort.SessionOptions()
    session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    
    session = ort.InferenceSession(
        onnx_path,
        sess_options=session_options,
        providers=providers
    )
    
    return session

# Example usage
def inference_example():
    """Example of running inference with NPU-optimized ONNX model."""
    
    # Load model and metadata
    onnx_path = "models/trading_agents/onnx/agent_final.onnx"
    metadata_path = "models/trading_agents/onnx/agent_final_metadata.json"
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Create NPU session
    session = create_npu_session(onnx_path)
    
    # Prepare input data (replace with actual agent state)
    input_dim = metadata['model_info']['input_dim']
    state_vector = np.random.randn(1, input_dim).astype(np.float32)
    
    # Run inference on NPU
    outputs = session.run(None, {'state_vector': state_vector})
    trading_matrix_flat = outputs[0]
    
    # Reshape to trading matrix
    num_items = metadata['model_info']['num_items']
    trading_matrix = trading_matrix_flat.reshape(num_items, num_items)
    
    print(f"Trading matrix shape: {trading_matrix.shape}")
    print(f"NPU inference completed successfully!")
    
    return trading_matrix

if __name__ == "__main__":
    inference_example()
'''
        
        return example_code
    
    def save_inference_example(self) -> None:
        """Save NPU inference example to file."""
        example_code = self.create_npu_inference_example()
        example_path = os.path.join(self.onnx_output_dir, 'npu_inference_example.py')
        
        try:
            with open(example_path, 'w') as f:
                f.write(example_code)
            logger.info(f"NPU inference example saved: {example_path}")
        except Exception as e:
            logger.error(f"Failed to save inference example: {e}")


def main():
    """
    Main function for command-line usage of ONNX converter.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert BlockMarket Trading Agent models to ONNX format for NPU acceleration'
    )
    parser.add_argument(
        '--model-path', 
        type=str,
        help='Specific .pth model file to convert (if not provided, converts all models)'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.pth',
        help='Glob pattern for finding .pth files (default: *.pth)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate existing ONNX models, do not convert'
    )
    parser.add_argument(
        '--create-example',
        action='store_true',
        help='Create NPU inference example code'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load config
        if os.path.exists(args.config):
            config = load_config()
        else:
            logger.error(f"Config file not found: {args.config}")
            return 1
        
        # Create converter
        converter = ONNXConverter(config)
        
        if args.create_example:
            converter.save_inference_example()
            logger.info("NPU inference example created")
            return 0
        
        if args.model_path:
            # Convert single model
            if not os.path.exists(args.model_path):
                logger.error(f"Model file not found: {args.model_path}")
                return 1
            
            success = converter.convert_single_model(args.model_path)
            return 0 if success else 1
        else:
            # Convert all models
            results = converter.convert_all_models(args.pattern)
            
            if not results:
                logger.warning("No models found to convert")
                return 1
            
            # Create inference example
            converter.save_inference_example()
            
            # Summary
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            
            logger.info(f"Conversion summary: {successful}/{total} models converted successfully")
            return 0 if successful == total else 1
            
    except Exception as e:
        logger.error(f"Conversion process failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
