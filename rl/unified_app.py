#!/usr/bin/env python3
"""
Unified application that combines Flask web server with Socket.IO client functionality.
This allows the trading environment to both serve a web interface and respond to external
socket events simultaneously.
"""

import threading
import time
import logging
import socketio
import json
from typing import Dict, Any, Optional
from flask import Flask

from config import load_config
from utils import setup_logging, validate_config
from training import create_training_environment
from web_server import create_app
from environment import TradingEnvironment
from agent import TradingAgent

logger = logging.getLogger(__name__)


class UnifiedTradingApp:
    """
    Unified application that manages both Flask web server and Socket.IO client.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the unified trading application.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.env: Optional[TradingEnvironment] = None
        self.flask_app: Optional[Flask] = None
        self.sio: Optional[socketio.Client] = None
        
        # Shared state for web interface
        self.current_state = {
            'timestep': 0,
            'generation': 0,
            'total_agents': 0,
            'recent_trades': 0,
            'avg_fitness': 0,
            'best_fitness': 0,
            'generation_progress': 0,
            'socket_connected': False,
            'external_simulation_running': False
        }
        
        # Control flags
        self.running_flag = {'value': True}
        self.training_thread: Optional[threading.Thread] = None
        self.flask_thread: Optional[threading.Thread] = None
        self.external_simulation_running = False
        self.external_simulation_thread: Optional[threading.Thread] = None
        
        # Initialize components
        self._setup_environment()
        self._setup_flask_app()
        if config.get('socket', {}).get('enabled', False):
            self._setup_socket_client()
    
    def _setup_environment(self):
        """Setup the trading environment."""
        logger.info("Creating trading environment...")
        self.env = create_training_environment(self.config)
        self.current_state.update({
            'total_agents': len(self.env.agents),
            'generation': self.env.current_generation,
            'timestep': self.env.current_timestep
        })
    
    def _setup_flask_app(self):
        """Setup the Flask web application."""
        logger.info("Setting up Flask web application...")
        self.flask_app = create_app(self.current_state, self.env)
        
        # Add socket status endpoints
        @self.flask_app.route('/socket_status')
        def socket_status():
            from flask import jsonify
            return jsonify({
                'connected': self.sio.connected if self.sio else False,
                'external_simulation_running': self.external_simulation_running,
                'socket_enabled': self.config.get('socket', {}).get('enabled', False)
            })
    
    def _setup_socket_client(self):
        """Setup the Socket.IO client."""
        socket_config = self.config.get('socket', {})
        server_url = socket_config.get('server_url', 'http://localhost:3001')
        namespace = socket_config.get('namespace', '/model')
        
        logger.info(f"Setting up Socket.IO client for {server_url}{namespace}")
        
        self.sio = socketio.Client(
            logger=False,  # Disable socket.io logging to reduce noise
            engineio_logger=False,
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=1
        )
        
        self._setup_socket_handlers()
    
    def _setup_socket_handlers(self):
        """Setup Socket.IO event handlers."""
        namespace = self.config.get('socket', {}).get('namespace', '/model')
        
        @self.sio.event(namespace=namespace)
        def connect():
            logger.info(f"✅ Connected to Socket.IO server at namespace {namespace}")
            self.current_state['socket_connected'] = True
            
        @self.sio.event(namespace=namespace)
        def connect_error(data):
            logger.error(f"❌ Socket connection error: {data}")
            self.current_state['socket_connected'] = False
            
        @self.sio.event(namespace=namespace)
        def disconnect():
            logger.info("🔌 Disconnected from Socket.IO server")
            self.current_state['socket_connected'] = False
            self._stop_external_simulation()
            
        @self.sio.event(namespace=namespace)
        def start_simulation(data):
            """
            Handle start_simulation event from external server.
            
            Expected data format:
            {
                "botInventoryMap": {
                    "0-0": {"diamond": 5, "gold": 10, "apple": 3, "emerald": 2, "redstone": 8},
                    "0-1": {"diamond": 3, "gold": 8, "apple": 5, "emerald": 4, "redstone": 6},
                    ...
                }
            }
            """
            logger.info("🚀 Received start_simulation command from external server!")
            logger.info(f"📊 Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            logger.debug(f"Full simulation data: {json.dumps(data, indent=2)}")
            
            try:
                self._start_external_simulation(data)
            except Exception as e:
                logger.error(f"❌ Failed to start external simulation: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                if self.sio and self.sio.connected:
                    self.sio.emit('simulation_error', {'error': str(e)}, namespace=namespace)
        
        @self.sio.event(namespace=namespace)
        def stop_simulation(data=None):
            """Handle stop_simulation event from external server."""
            logger.info("Received stop_simulation command from external server")
            self._stop_external_simulation()
    
    def _start_external_simulation(self, data: Dict[str, Any]):
        """
        Start external simulation with provided data.
        This runs separately from the internal training loop.
        
        Args:
            data: Simulation data containing botInventoryMap
        """
        if self.external_simulation_running:
            logger.warning("External simulation already running, stopping previous simulation")
            self._stop_external_simulation()
        
        # Parse bot inventory data
        bot_inventory_map = data.get('botInventoryMap', {})
        if not bot_inventory_map:
            raise ValueError("No botInventoryMap provided in simulation data")
        
        # Create a separate environment for external simulation
        external_env = TradingEnvironment(self.config)
        
        # Parse agents configuration
        agents_config = self._parse_bot_inventory_map(bot_inventory_map)
        if not agents_config:
            raise ValueError("No valid agents found in botInventoryMap")
        
        # Create agents from configuration
        agents = self._create_agents_from_config(agents_config, external_env)
        
        # Initialize environment with custom agents
        external_env.agents = agents
        external_env.population_size = len(agents)
        
        # Initialize agent positions
        for agent in agents:
            external_env.agent_positions[agent.agent_id] = agent.position
        
        # Start external simulation in separate thread
        self.external_simulation_running = True
        self.current_state['external_simulation_running'] = True
        self.external_simulation_thread = threading.Thread(
            target=self._run_external_simulation,
            args=(external_env,),
            daemon=True
        )
        self.external_simulation_thread.start()
        
        # Notify server that simulation started
        if self.sio and self.sio.connected:
            namespace = self.config.get('socket', {}).get('namespace', '/model')
            self.sio.emit('simulation_started', {
                'agents_count': len(agents),
                'items': list(self.config['environment']['items_list'])
            }, namespace=namespace)
    
    def _stop_external_simulation(self):
        """Stop the running external simulation."""
        if self.external_simulation_running:
            logger.info("Stopping external simulation...")
            self.external_simulation_running = False
            self.current_state['external_simulation_running'] = False
            
            if self.external_simulation_thread and self.external_simulation_thread.is_alive():
                self.external_simulation_thread.join(timeout=5.0)
            
            # Notify server
            if self.sio and self.sio.connected:
                namespace = self.config.get('socket', {}).get('namespace', '/model')
                self.sio.emit('simulation_stopped', {}, namespace=namespace)
    
    def _run_external_simulation(self, external_env: TradingEnvironment):
        """Run the external simulation loop."""
        logger.info("Starting external simulation...")
        
        try:
            timestep = 0
            while self.external_simulation_running and self.running_flag['value']:
                # Execute one simulation step
                step_info = external_env.step()
                
                # Debug logging
                logger.debug(f"Timestep {timestep}: trades_executed={step_info['trades_executed']}, total_trades_in_history={len(external_env.trade_history) if hasattr(external_env, 'trade_history') else 'No history'}")
                
                # Always try to emit trade data (even if 0 trades) for debugging
                self._emit_trade_data(external_env, step_info, timestep)
                
                timestep += 1
                
                # Small delay to prevent overwhelming the socket
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"External simulation error: {e}")
            if self.sio and self.sio.connected:
                namespace = self.config.get('socket', {}).get('namespace', '/model')
                self.sio.emit('simulation_error', {'error': str(e)}, namespace=namespace)
        finally:
            self.external_simulation_running = False
            self.current_state['external_simulation_running'] = False
            logger.info("External simulation stopped")
    
    def _emit_trade_data(self, external_env: TradingEnvironment, step_info: Dict[str, Any], timestep: int):
        """
        Emit trade data to the Socket.IO server.
        
        Args:
            external_env: The external simulation environment
            step_info: Information about the simulation step
            timestep: Current timestep
        """
        try:
            # Format trade data for emission
            trade_data = {
                'timestep': timestep,
                'generation': step_info.get('generation', 0),
                'trades_count': step_info['trades_executed'],
                'trades': []
            }
            
            # Debug logging
            logger.debug(f"_emit_trade_data called: timestep={timestep}, trades_executed={step_info['trades_executed']}")
            logger.debug(f"Environment has trade_history: {hasattr(external_env, 'trade_history')}")
            if hasattr(external_env, 'trade_history'):
                logger.debug(f"Trade history length: {len(external_env.trade_history)}")
            
            # Get recent trades from environment
            if hasattr(external_env, 'trade_history') and external_env.trade_history and step_info['trades_executed'] > 0:
                # Get trades from this timestep
                recent_trades = []
                trades_to_process = external_env.trade_history[-step_info['trades_executed']:]
                logger.debug(f"Processing {len(trades_to_process)} trades from history")
                
                for trade in trades_to_process:
                    logger.debug(f"Processing trade: {trade}")
                    # Extract trade data from environment format
                    requester_gave = trade.get('requester_gave', (None, None))
                    requester_received = trade.get('requester_received', (None, None))
                    
                    trade_formatted = {
                        'requester_id': trade.get('requester_id'),
                        'target_id': trade.get('target_id'),
                        'item_given': requester_gave[0] if requester_gave else None,
                        'amount_given': requester_gave[1] if requester_gave else None,
                        'item_received': requester_received[0] if requester_received else None,
                        'amount_received': requester_received[1] if requester_received else None,
                        'requester_cell': getattr(self._get_agent_by_id(external_env, trade.get('requester_id')), 'cell_key', None),
                        'target_cell': getattr(self._get_agent_by_id(external_env, trade.get('target_id')), 'cell_key', None)
                    }
                    
                    logger.debug(f"Formatted trade: {trade_formatted}")
                    recent_trades.append(trade_formatted)
                
                trade_data['trades'] = recent_trades
            
            # Always emit trade data (even if empty) for debugging
            if self.sio and self.sio.connected:
                namespace = self.config.get('socket', {}).get('namespace', '/model')
                logger.debug(f"Emitting to namespace {namespace}: {trade_data}")
                self.sio.emit('trade', trade_data, namespace=namespace)
                logger.info(f"✅ Emitted trade data for timestep {timestep}: {len(trade_data['trades'])} trades")
            else:
                logger.warning(f"❌ Socket not connected, cannot emit trade data for timestep {timestep}")
            
        except Exception as e:
            logger.error(f"Failed to emit trade data: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _get_agent_by_id(self, env: TradingEnvironment, agent_id: str) -> Optional[TradingAgent]:
        """Get agent by ID from environment."""
        if not env or not agent_id:
            return None
            
        for agent in env.agents:
            if agent.agent_id == agent_id:
                return agent
        return None
    
    def _parse_bot_inventory_map(self, bot_inventory_map: Dict[str, Dict[str, int]]) -> list:
        """Parse the botInventoryMap into agent configurations."""
        agents_config = []
        
        for cell_key, inventory_data in bot_inventory_map.items():
            try:
                # Parse cell position from "row-col" format
                row, col = map(int, cell_key.split('-'))
                
                # Create agent config
                agent_config = {
                    'cell_key': cell_key,
                    'position': [row, col],
                    'inventory': inventory_data,
                    'agent_id': f"agent_{cell_key}"
                }
                
                agents_config.append(agent_config)
                
            except ValueError as e:
                logger.warning(f"Invalid cell key format '{cell_key}': {e}")
                continue
                
        logger.info(f"Parsed {len(agents_config)} agents from botInventoryMap")
        return agents_config
    
    def _create_agents_from_config(self, agents_config: list, env: TradingEnvironment) -> list:
        """Create TradingAgent instances from parsed configuration."""
        agents = []
        items_list = list(self.config['environment']['items_list'])
        
        for agent_config in agents_config:
            try:
                # Validate and filter inventory to only include known items
                original_inventory = agent_config['inventory']
                filtered_inventory = {}
                
                for item, amount in original_inventory.items():
                    if item in items_list:
                        filtered_inventory[item] = amount
                    else:
                        logger.warning(f"Ignoring unknown item '{item}' for agent {agent_config['agent_id']}")
                
                # Ensure all environment items are present (set to 0 if missing)
                for item in items_list:
                    if item not in filtered_inventory:
                        filtered_inventory[item] = 0
                
                # Choose random desired item
                import random
                desired_item = random.choice(items_list)
                
                # Create agent
                agent = TradingAgent(
                    agent_id=agent_config['agent_id'],
                    config=self.config,
                    items_list=items_list,
                    desired_item=desired_item,
                    initial_inventory=filtered_inventory
                )
                
                # Set position and cell key
                agent.position = agent_config['position']
                agent.cell_key = agent_config['cell_key']
                
                # Debug logging
                logger.debug(f"Created agent {agent.agent_id}: inventory={agent.inventory}, desired={agent.desired_item}")
                logger.debug(f"Agent trading matrix:\n{agent.trading_matrix}")
                
                agents.append(agent)
                
            except Exception as e:
                logger.error(f"Failed to create agent {agent_config['agent_id']}: {e}")
                continue
        
        logger.info(f"Created {len(agents)} trading agents for external simulation")
        return agents
    
    def start_flask_server(self):
        """Start the Flask web server in a separate thread."""
        if not self.flask_app:
            logger.error("Flask app not initialized")
            return False
        
        def run_server():
            try:
                self.flask_app.run(
                    host=self.config['server']['host'],
                    port=self.config['server']['port'],
                    debug=self.config['server']['debug'],
                    use_reloader=False  # Disable reloader to avoid issues with threading
                )
            except Exception as e:
                logger.error(f"Flask server error: {e}")
        
        self.flask_thread = threading.Thread(target=run_server, daemon=True)
        self.flask_thread.start()
        
        logger.info(f"🌐 Flask web server started on {self.config['server']['host']}:{self.config['server']['port']}")
        return True
    
    def connect_socket_client(self):
        """Connect the Socket.IO client."""
        if not self.sio:
            logger.warning("Socket.IO client not initialized")
            return False
        
        socket_config = self.config.get('socket', {})
        server_url = socket_config.get('server_url', 'http://localhost:3001')
        namespace = socket_config.get('namespace', '/model')
        
        try:
            logger.info(f"🔌 Connecting to Socket.IO server at {server_url}...")
            
            # Add headers for ngrok if needed
            headers = {}
            if 'ngrok' in server_url:
                headers['ngrok-skip-browser-warning'] = 'true'
            
            # Extract base URL and connect
            base_url = server_url.replace(namespace, '')
            
            self.sio.connect(
                base_url,
                headers=headers,
                transports=['websocket', 'polling'],
                wait_timeout=10,
                namespaces=[namespace]
            )
            
            # Wait a moment to ensure connection is established
            time.sleep(1)
            
            if self.sio.connected:
                logger.info("✅ Socket.IO client connected successfully!")
                self.current_state['socket_connected'] = True
                return True
            else:
                logger.error("❌ Socket.IO connection failed - not connected")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect Socket.IO client: {e}")
            return False
    
    def start_internal_training(self):
        """Start the internal training loop in a separate thread."""
        if not self.env:
            logger.error("Environment not initialized")
            return False
        
        def training_wrapper():
            try:
                from training import training_loop
                training_loop(
                    env=self.env,
                    simulation_speed=self.config['training']['simulation_speed'],
                    log_frequency=self.config['training']['log_frequency'],
                    model_save_frequency=self.config['training']['model_save_frequency'],
                    model_save_path=self.config['training']['model_save_path'],
                    max_generations=self.config['training']['max_generations'],
                    target_fitness=self.config['training']['target_fitness'],
                    early_stopping_patience=self.config['training']['early_stopping_patience'],
                    current_state=self.current_state,
                    running_flag=self.running_flag
                )
            except Exception as e:
                logger.error(f"Training loop error: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        self.training_thread = threading.Thread(target=training_wrapper, daemon=True)
        self.training_thread.start()
        
        logger.info("🚀 Internal training loop started")
        return True
    
    def run(self, enable_training=True, enable_flask=True, enable_socket=None):
        """
        Run the unified application.
        
        Args:
            enable_training: Whether to start internal training
            enable_flask: Whether to start Flask web server
            enable_socket: Whether to enable socket client (None = use config)
        """
        logger.info("="*60)
        logger.info("🏪 Starting Unified Trading Application")
        logger.info("="*60)
        
        # Start Flask server
        if enable_flask:
            if not self.start_flask_server():
                logger.error("Failed to start Flask server")
                return False
        
        # Connect socket client
        socket_enabled = enable_socket if enable_socket is not None else self.config.get('socket', {}).get('enabled', False)
        if socket_enabled and self.config.get('socket', {}).get('auto_connect', True):
            self.connect_socket_client()
        
        # Start internal training
        if enable_training:
            if not self.start_internal_training():
                logger.error("Failed to start internal training")
                return False
        
        logger.info("✅ All components started successfully")
        
        if enable_flask:
            logger.info(f"🌐 Web interface: http://localhost:{self.config['server']['port']}")
        if socket_enabled:
            logger.info(f"🔌 Socket.IO client: {self.config.get('socket', {}).get('server_url', 'Not configured')}")
        
        return True
    
    def shutdown(self):
        """Shutdown the application gracefully."""
        logger.info("Shutting down unified application...")
        
        # Stop all running components
        self.running_flag['value'] = False
        self._stop_external_simulation()
        
        # Disconnect socket client
        if self.sio and self.sio.connected:
            self.sio.disconnect()
        
        # Wait for threads to finish
        for thread in [self.training_thread, self.external_simulation_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=5.0)
        
        # Give Flask server time to finish
        if self.flask_thread:
            time.sleep(2)
        
        logger.info("🏁 Unified application shutdown complete")


def main():
    """Main function to run the unified trading application."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified Multi-Agent Trading Application')
    parser.add_argument('--config', default='config.yaml', help='Configuration file path')
    parser.add_argument('--no-web', action='store_true', help='Disable web interface')
    parser.add_argument('--no-training', action='store_true', help='Disable internal training')
    parser.add_argument('--no-socket', action='store_true', help='Disable socket client')
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


if __name__ == "__main__":
    exit(main())
