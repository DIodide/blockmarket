# ONNX Model Conversion for NPU Acceleration

This document explains how to convert BlockMarket trading agent models from PyTorch (.pth) format to ONNX format for NPU acceleration on Qualcomm Snapdragon X Elite devices.

## Overview

The ONNX conversion system enables trading agent neural networks to leverage the 45 TOPS of AI performance available on Snapdragon X Elite NPUs, providing significant acceleration for real-time inference during trading decisions.

## Features

- **Automatic Model Discovery**: Finds all .pth files in the models directory
- **Batch Conversion**: Convert all models at once or individual models
- **Model Validation**: Verifies ONNX models produce identical outputs to PyTorch versions
- **NPU Optimization Metadata**: Includes optimization hints for Qualcomm NPU deployment
- **Usage Examples**: Generates ready-to-use inference code

## Quick Start

### 1. Install Dependencies

```bash
cd blockmarket/rl
pip install -r requirements.txt
```

### 2. Convert All Models

```bash
python convert_models.py
```

### 3. Convert Specific Model

```bash
python convert_models.py --model-path models/trading_agents/agent_final.pth
```

### 4. Generate NPU Usage Example

```bash
python convert_models.py --create-example
```

## Detailed Usage

### Command Line Options

```bash
python convert_models.py [OPTIONS]

Options:
  --model-path PATH     Convert specific .pth model file
  --pattern PATTERN     Glob pattern for finding .pth files (default: *.pth)  
  --config PATH         Path to configuration file (default: config.yaml)
  --validate-only       Only validate existing ONNX models, do not convert
  --create-example      Create NPU inference example code
  --help               Show help message
```

### Programmatic Usage

```python
from onnx_conversion import ONNXConverter

# Create converter
converter = ONNXConverter()

# Convert all models
results = converter.convert_all_models()

# Convert specific model
success = converter.convert_single_model('path/to/model.pth')

# Create NPU inference example
converter.save_inference_example()
```

## Output Structure

After conversion, the following files are created in `models/trading_agents/onnx/`:

```
models/trading_agents/onnx/
├── agent_final.onnx                    # ONNX model
├── agent_final_metadata.json          # Model metadata and NPU hints
├── agent_gen50_rank1.onnx             # Another converted model
├── agent_gen50_rank1_metadata.json    # Corresponding metadata
└── npu_inference_example.py           # Usage example code
```

## Metadata Format

Each ONNX model includes a metadata JSON file with the following information:

```json
{
  "model_info": {
    "onnx_path": "agent_final.onnx",
    "model_type": "TradingNetwork", 
    "input_dim": 131,
    "output_dim": 25,
    "items_list": ["diamond", "gold", "apple", "emerald", "redstone"],
    "num_items": 5,
    "validation_passed": true
  },
  "agent_info": {
    "agent_id": "agent_0",
    "desired_item": "diamond",
    "training_history": 1250
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
    "torch_version": "2.0.1",
    "onnx_version": "1.14.0"
  }
}
```

## NPU Inference Example

The converter automatically generates an example showing how to use the ONNX models with NPU acceleration:

```python
import onnxruntime as ort
import numpy as np
import json

# Configure ONNX Runtime for NPU acceleration
def create_npu_session(onnx_path: str):
    providers = [
        ('QNNExecutionProvider', {
            'backend_path': 'QnnHtp.dll',
            'profiling_level': 'basic',
            'rpc_control_latency': 1000,
            'vtcm_mb': 8,
            'htp_performance_mode': 'burst'
        }),
        'CPUExecutionProvider'  # Fallback
    ]
    
    session_options = ort.SessionOptions()
    session_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    
    return ort.InferenceSession(onnx_path, sess_options=session_options, providers=providers)

# Run inference
session = create_npu_session("models/trading_agents/onnx/agent_final.onnx")
outputs = session.run(None, {'state_vector': input_data})
```

## Integration with Training System

### Automatic Conversion After Training

You can integrate ONNX conversion into the training pipeline by modifying the model saving process:

```python
from onnx_conversion import ONNXConverter

# In training.py or after training completes
def save_and_convert_models(env, model_save_path, generation):
    # Save PyTorch models (existing functionality)
    save_generation_models(env, model_save_path, generation)
    
    # Convert to ONNX for NPU deployment
    converter = ONNXConverter()
    converter.convert_all_models()
```

### Real-time NPU Inference

Replace PyTorch inference in the `TradingAgent` class with ONNX NPU inference:

```python
class NPUTradingAgent(TradingAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.onnx_session = None
        
    def load_onnx_model(self, onnx_path: str):
        """Load ONNX model for NPU inference."""
        self.onnx_session = create_npu_session(onnx_path)
    
    def update_trading_matrix(self, market_data=None):
        """NPU-accelerated trading matrix update."""
        if self.onnx_session:
            state = self.get_state_vector(market_data)
            outputs = self.onnx_session.run(None, {'state_vector': state.numpy()})
            matrix_update = outputs[0].reshape(self.num_items, self.num_items)
            # Apply update with learning rate
            learning_rate = self.config['learning']['matrix_update_rate']
            self.trading_matrix = (1 - learning_rate) * self.trading_matrix + learning_rate * matrix_update
        else:
            # Fallback to PyTorch
            super().update_trading_matrix(market_data)
```

## Performance Expectations

On Qualcomm Snapdragon X Elite with NPU acceleration:

- **Inference Latency**: ~0.1-1ms per agent decision (vs 10-50ms on CPU)
- **Throughput**: Up to 1000+ agent updates per second
- **Power Efficiency**: ~10x more efficient than CPU-only inference
- **Scalability**: Support for 100+ concurrent trading agents in real-time

## Troubleshooting

### Common Issues

1. **ONNX Runtime Not Found**
   ```bash
   pip install onnxruntime>=1.15.0
   ```

2. **QNN Provider Not Available**
   - Ensure you're running on a Snapdragon X Elite device
   - Install Qualcomm AI Stack for Windows/Linux
   - Check that QnnHtp.dll is available in PATH

3. **Model Validation Failed**
   - Check PyTorch and ONNX versions are compatible
   - Verify input tensor shapes match expected dimensions
   - Try reducing numerical tolerance for validation

4. **No .pth Files Found**
   - Ensure you've run training and models have been saved
   - Check the `model_save_path` in config.yaml
   - Verify file permissions

### Debug Mode

Enable verbose logging for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

converter = ONNXConverter()
converter.convert_all_models()
```

## Advanced Configuration

### Custom ONNX Export Settings

```python
converter = ONNXConverter()

# Custom export with different opset version
converter.convert_to_onnx(
    model, 
    "output.onnx", 
    opset_version=13,  # Use newer opset
    dynamic_axes={'state_vector': {0: 'batch_size', 1: 'sequence_length'}}
)
```

### Quantization for Better NPU Performance

```python
import onnxruntime.quantization as quantization

# Quantize model for better NPU performance
quantization.quantize_dynamic(
    "model.onnx",
    "model_quantized.onnx", 
    weight_type=quantization.QuantType.QUInt8
)
```

## Contributing

When adding new neural network architectures to the BlockMarket system:

1. Ensure your network inherits from `nn.Module`
2. Add conversion support in `ONNXConverter.load_pytorch_model()`
3. Update input/output dimension calculations
4. Test ONNX conversion and validation
5. Update metadata generation as needed

## References

- [ONNX Runtime Documentation](https://onnxruntime.ai/docs/)
- [Qualcomm AI Stack](https://developer.qualcomm.com/software/qualcomm-ai-stack)
- [PyTorch ONNX Export](https://pytorch.org/docs/stable/onnx.html)
- [BlockMarket Trading System](../README.md)
