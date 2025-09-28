#!/usr/bin/env python3
"""
Test script to verify trade emission is working correctly.
"""

import logging
import sys
import time
from unified_app import UnifiedTradingApp
from config import load_config
from utils import setup_logging

# Setup logging to see debug output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_trade_emission():
    """Test that trades are being generated and emitted properly."""
    print("🧪 Testing trade emission...")
    
    # Load config
    config = load_config()
    
    # Override config for testing
    config['socket']['enabled'] = False  # Don't try to connect to external socket
    config['environment']['population_size'] = 3  # Small population for testing
    config['environment']['generation_length'] = 20  # Short generation
    config['training']['simulation_speed'] = 0.0  # Fast simulation
    config['logging']['level'] = 'DEBUG'
    
    # Create unified app
    app = UnifiedTradingApp(config)
    
    # Create test bot inventory map
    test_inventory_map = {
        "0-0": {"diamond": 5, "gold": 10, "apple": 3, "emerald": 2, "redstone": 8},
        "1-1": {"diamond": 3, "gold": 8, "apple": 15, "emerald": 4, "redstone": 6},
        "2-2": {"diamond": 8, "gold": 2, "apple": 5, "emerald": 10, "redstone": 3}
    }
    
    try:
        print("📊 Starting external simulation with test data...")
        
        # Start external simulation
        app._start_external_simulation({'botInventoryMap': test_inventory_map})
        
        print("⏱️ Running simulation for 10 seconds...")
        time.sleep(10)
        
        print("🛑 Stopping simulation...")
        app._stop_external_simulation()
        
        print("✅ Test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        app.shutdown()

if __name__ == "__main__":
    test_trade_emission()
