#!/usr/bin/env python3
"""
Debug script to understand why trades aren't being emitted.
"""

import logging
import sys
import os

# Add current directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import load_config
from utils import setup_logging

# Setup detailed logging
def setup_debug_logging():
    """Setup detailed debug logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('debug_trades.log')
        ]
    )
    
    # Set specific loggers to DEBUG
    logging.getLogger('__main__').setLevel(logging.DEBUG)
    logging.getLogger('unified_app').setLevel(logging.DEBUG)
    logging.getLogger('environment').setLevel(logging.DEBUG)
    logging.getLogger('agent').setLevel(logging.DEBUG)

def main():
    """Main debug function."""
    setup_debug_logging()
    logger = logging.getLogger(__name__)
    
    print("🐛 Debug: Starting trade emission debug...")
    
    try:
        # Load config
        config = load_config()
        
        # Override config for debugging
        config['logging']['level'] = 'DEBUG'
        config['socket']['enabled'] = False  # Don't try to connect to external socket
        config['environment']['population_size'] = 3
        config['environment']['generation_length'] = 10
        config['training']['simulation_speed'] = 0.0
        
        logger.info("Config loaded and modified for debugging")
        
        # Import here after setting up logging
        from unified_app import UnifiedTradingApp
        
        # Create unified app
        logger.info("Creating UnifiedTradingApp...")
        app = UnifiedTradingApp(config)
        
        # Create test inventory map with diverse inventories to encourage trading
        test_inventory_map = {
            "0-0": {"diamond": 10, "gold": 0, "apple": 0, "emerald": 0, "redstone": 0},
            "1-1": {"diamond": 0, "gold": 10, "apple": 0, "emerald": 0, "redstone": 0},
            "2-2": {"diamond": 0, "gold": 0, "apple": 10, "emerald": 0, "redstone": 0}
        }
        
        logger.info("Starting external simulation with test data...")
        logger.info(f"Test inventory map: {test_inventory_map}")
        
        # Start external simulation
        app._start_external_simulation({'botInventoryMap': test_inventory_map})
        
        # Let it run for a few timesteps
        import time
        logger.info("Running simulation for 5 seconds...")
        time.sleep(5)
        
        logger.info("Stopping simulation...")
        app._stop_external_simulation()
        
        logger.info("Debug completed!")
        
    except Exception as e:
        logger.error(f"Debug failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        if 'app' in locals():
            app.shutdown()

if __name__ == "__main__":
    main()
