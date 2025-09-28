#!/usr/bin/env python3
"""
Main entry point for the multi-agent trading environment.
This now supports both the original training mode and the new unified mode
that combines Flask web server with Socket.IO client functionality.
"""

import argparse
import logging
import sys
import os

from config import load_config
from utils import setup_logging, validate_config


def main():
    """Main function to run the trading environment."""
    parser = argparse.ArgumentParser(description='Multi-Agent Trading Environment')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--mode', choices=['training', 'unified', 'socket-only'], default='unified',
                       help='Run mode: training (original), unified (Flask+Socket+Training), socket-only (Socket client only)')
    parser.add_argument('--no-web', action='store_true', help='Disable web interface (unified mode only)')
    parser.add_argument('--no-training', action='store_true', help='Disable internal training (unified mode only)')
    parser.add_argument('--no-socket', action='store_true', help='Disable socket client (unified mode only)')
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
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    # Run in selected mode
    if args.mode == 'training':
        return run_training_mode(config, args, logger)
    elif args.mode == 'unified':
        return run_unified_mode(config, args, logger)
    elif args.mode == 'socket-only':
        return run_socket_only_mode(config, args, logger)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        return 1


def run_training_mode(config, args, logger):
    """Run the original training-only mode."""
    import threading
    import time
    from training import create_training_environment, training_loop
    from web_server import create_app
    
    logger.info("="*60)
    logger.info("🏪 Multi-Agent Trading Environment Starting (Training Mode)")
    logger.info("="*60)
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
                use_reloader=False
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
    except Exception as e:
        logger.error(f"Training failed: {e}")
        running_flag['value'] = False
        return 1
    finally:
        logger.info("Shutting down...")
        running_flag['value'] = False
        
        if not args.no_web:
            time.sleep(2)
    
    logger.info("="*60)
    logger.info("🏁 Multi-Agent Trading Environment Finished")
    logger.info("="*60)
    
    return 0


def run_unified_mode(config, args, logger):
    """Run the new unified mode with Flask + Socket.IO + Training."""
    try:
        from unified_app import UnifiedTradingApp
    except ImportError as e:
        logger.error(f"Failed to import unified app: {e}")
        logger.error("Make sure unified_app.py is available and socketio is installed")
        return 1
    
    logger.info("="*60)
    logger.info("🏪 Starting Unified Trading Application")
    logger.info("="*60)
    
    # Create and run unified app
    app = UnifiedTradingApp(config)
    
    try:
        success = app.run(
            enable_training=not args.no_training,
            enable_flask=not args.no_web,
            enable_socket=not args.no_socket
        )
        
        if not success:
            return 1
        
        # Keep running until interrupted
        logger.info("Press Ctrl+C to stop...")
        import time
        while app.running_flag['value']:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1
    finally:
        app.shutdown()
    
    return 0


def run_socket_only_mode(config, args, logger):
    """Run socket client only mode."""
    try:
        from socket_client import SocketSimulationClient
    except ImportError as e:
        logger.error(f"Failed to import socket client: {e}")
        logger.error("Make sure socket_client.py is available and socketio is installed")
        return 1
    
    logger.info("="*60)
    logger.info("🔌 Starting Socket Client Only Mode")
    logger.info("="*60)
    
    # Get socket URL from config
    socket_config = config.get('socket', {})
    server_url = socket_config.get('server_url', 'http://localhost:3001')
    namespace = socket_config.get('namespace', '/model')
    full_url = f"{server_url}{namespace}"
    
    logger.info(f"Connecting to: {full_url}")
    
    # Create and connect client
    client = SocketSimulationClient(full_url)
    
    if client.connect():
        logger.info("Socket client connected successfully")
        logger.info("Waiting for start_simulation command...")
        
        try:
            import time
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            client.disconnect()
    else:
        logger.error("Failed to connect to socket server")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
