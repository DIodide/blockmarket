#!/usr/bin/env python3
"""
Main entry point for the multi-agent trading environment.
"""

import argparse
import threading
import time
import logging

from config import load_config
from utils import setup_logging, validate_config
from training import create_training_environment, training_loop
from web_server import create_app


def main():
    """Main function to run the trading environment."""
    parser = argparse.ArgumentParser(description='Multi-Agent Trading Environment')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--no-web', action='store_true', help='Disable web interface')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    if not validate_config(config):
        print("❌ Invalid configuration. Please check your config file.")
        return 1
    
    if args.debug:
        config['logging']['level'] = 'DEBUG'
        config['server']['debug'] = True
    
    # Setup logging
    log_file, log_mode = setup_logging(config)
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("🏪 Multi-Agent Trading Environment Starting")
    logger.info("="*60)
    logger.info(f"Configuration loaded from: {args.config}")
    logger.info(f"Logging to: {log_file} ({log_mode})")
    logger.info(f"Population size: {config['environment']['population_size']}")
    logger.info(f"Items: {config['environment']['items_list']}")
    logger.info(f"Max generations: {config['training']['max_generations']}")
    
    # Create environment
    logger.info("Creating trading environment...")
    env = create_training_environment(config)
    
    # Shared state for web interface
    current_state = {
        'timestep': 0,
        'generation': 0,
        'total_agents': len(env.agents),
        'recent_trades': 0,
        'avg_fitness': 0,
        'best_fitness': 0,
        'generation_progress': 0
    }
    
    # Running flag for graceful shutdown
    running_flag = {'value': True}
    
    # Start web server if enabled
    if not args.no_web:
        logger.info(f"Starting web server on {config['server']['host']}:{config['server']['port']}")
        app = create_app(current_state, env)
        
        def run_server():
            app.run(
                host=config['server']['host'],
                port=config['server']['port'],
                debug=config['server']['debug'],
                use_reloader=False  # Disable reloader to avoid issues with threading
            )
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        logger.info(f"🌐 Web interface available at http://localhost:{config['server']['port']}")
    
    # Start training
    try:
        logger.info("Starting training loop...")
        training_loop(
            env=env,
            simulation_speed=config['training']['simulation_speed'],
            log_frequency=config['training']['log_frequency'],
            model_save_frequency=config['training']['model_save_frequency'],
            model_save_path=config['training']['model_save_path'],
            max_generations=config['training']['max_generations'],
            target_fitness=config['training']['target_fitness'],
            early_stopping_patience=config['training']['early_stopping_patience'],
            current_state=current_state,
            running_flag=running_flag
        )
        
    except KeyboardInterrupt:
        logger.info("Training interrupted by user")
        running_flag['value'] = False
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("This might be due to relative import issues. Try running from the parent directory.")
        running_flag['value'] = False
        return 1
    except Exception as e:
        logger.error(f"Training failed: {e}")
        running_flag['value'] = False
        return 1
    finally:
        logger.info("Shutting down...")
        running_flag['value'] = False
        
        # Give web server time to finish current requests
        if not args.no_web:
            time.sleep(2)
    
    logger.info("="*60)
    logger.info("🏁 Multi-Agent Trading Environment Finished")
    logger.info("="*60)
    
    return 0


if __name__ == "__main__":
    exit(main())
