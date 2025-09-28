#!/usr/bin/env python3
"""
Convenient CLI script for converting BlockMarket trading agent models to ONNX format.

This script provides an easy-to-use interface for converting PyTorch models (.pth files)
to ONNX format for NPU utilization on Qualcomm Snapdragon X Elite devices.

Usage:
    python convert_models.py                    # Convert all models
    python convert_models.py --help             # Show help
    python convert_models.py --model agent.pth  # Convert specific model
    python convert_models.py --create-example   # Generate NPU usage example
"""

import sys
import os
import logging

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from onnx_conversion import main as onnx_main

def main():
    """Main entry point for the conversion script."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    print("🔄 BlockMarket ONNX Model Converter")
    print("=" * 50)
    
    # Call the main ONNX conversion function
    return onnx_main()

if __name__ == "__main__":
    exit(main())
