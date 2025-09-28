#!/usr/bin/env python3
"""
Socket.IO client for connecting to external simulation controller.
Receives start_simulation commands and emits trade data.
"""

import socketio
import json
import logging
import threading
import time
from typing import Dict, Any, List
from agent import TradingAgent
from environment import TradingEnvironment
from config import load_config

logger = logging.getLogger(__name__)


class SocketSimulationClient:
    def __init__(self, socket_url: str):
        """
        Initialize Socket.IO client for simulation control.
        
        Args:
            socket_url: URL of the Socket.IO server (e.g., 'http://localhost:3000')
        """
        self.socket_url = socket_url
        self.sio = socketio.Client(
            logger=True,
            engineio_logger=True,
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=1
        )
        self.env = None
        self.simulation_running = False
        self.simulation_thread = None
        
        # Setup event handlers
        self._setup_event_handlers()
        
        # Load default config
        self.config = load_config()
        
    def _setup_event_handlers(self):
        """Setup Socket.IO event handlers."""
        
        @self.sio.event(namespace='/model')
        def connect():
            logger.info(f"✅ Connected to /model namespace at {self.socket_url}")
            logger.info("🎯 Ready to receive start_simulation events")
            
        @self.sio.event(namespace='/model')
        def connect_error(data):
            logger.error(f"❌ Connection error: {data}")
            
        @self.sio.event(namespace='/model')
        def disconnect():
            logger.info("🔌 Disconnected from /model namespace")
            self.stop_simulation()
            
        @self.sio.event(namespace='/model')
        def start_simulation(data):
            """
            Handle start_simulation event from server.
            
            Expected data format:
            {
                "botInventoryMap": {
                    "0-0": {"diamond": 5, "gold": 10, "apple": 3, "emerald": 2, "redstone": 8},
                    "0-1": {"diamond": 3, "gold": 8, "apple": 5, "emerald": 4, "redstone": 6},
                    ...
                }
            }
            """
            logger.info("🚀 Received start_simulation command from /model namespace!")
            logger.info(f"📊 Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            logger.debug(f"Full simulation data: {json.dumps(data, indent=2)}")
            
            try:
                self._start_simulation_with_data(data)
            except Exception as e:
                logger.error(f"❌ Failed to start simulation: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                self.sio.emit('simulation_error', {'error': str(e)}, namespace='/model')
        
        # Add a catch-all event handler for debugging
        @self.sio.event(namespace='/model')
        def catch_all(event, *args):
            logger.info(f"🔍 Received /model event '{event}' with args: {args}")
        
        @self.sio.event(namespace='/model')
        def stop_simulation(data=None):
            """Handle stop_simulation event from server."""
            logger.info("Received stop_simulation command from /model namespace")
            self.stop_simulation()
            
    def connect(self):
        """Connect to the Socket.IO server."""
        try:
            logger.info(f"🔌 Connecting to {self.socket_url}...")
            
            # Add headers for ngrok if needed
            headers = {}
            if 'ngrok' in self.socket_url:
                headers['ngrok-skip-browser-warning'] = 'true'
            
            # Extract base URL and connect to /model namespace
            base_url = self.socket_url.replace('/model', '')
            logger.info(f"🎯 Connecting to base URL: {base_url}")
            logger.info(f"🎯 Using namespace: /model")
            
            self.sio.connect(
                base_url,
                headers=headers,
                transports=['websocket', 'polling'],
                wait_timeout=10,
                namespaces=['/model']
            )
            
            # Wait a moment to ensure connection is established
            time.sleep(1)
            
            if self.sio.connected:
                logger.info("✅ Successfully connected!")
                return True
            else:
                logger.error("❌ Connection failed - not connected")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to {self.socket_url}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
            
    def disconnect(self):
        """Disconnect from the Socket.IO server."""
        if self.sio.connected:
            self.stop_simulation()
            self.sio.disconnect()
            
    def _parse_bot_inventory_map(self, bot_inventory_map: Dict[str, Dict[str, int]]) -> List[Dict]:
        """
        Parse the botInventoryMap into agent configurations.
        
        Args:
            bot_inventory_map: Map of cellKey -> inventory data
            
        Returns:
            List of agent configurations
        """
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
        
    def _create_agents_from_config(self, agents_config: List[Dict]) -> List[TradingAgent]:
        """
        Create TradingAgent instances from parsed configuration.
        
        Args:
            agents_config: List of agent configurations
            
        Returns:
            List of TradingAgent instances
        """
        agents = []
        items_list = list(self.config['environment']['items_list'])
        
        logger.info(f"Environment items: {items_list}")
        
        for agent_config in agents_config:
            try:
                # Validate and filter inventory to only include known items
                original_inventory = agent_config['inventory']
                filtered_inventory = {}
                
                logger.debug(f"Original inventory for {agent_config['agent_id']}: {original_inventory}")
                
                for item, amount in original_inventory.items():
                    if item in items_list:
                        filtered_inventory[item] = amount
                    else:
                        logger.warning(f"Ignoring unknown item '{item}' for agent {agent_config['agent_id']}")
                
                # Ensure all environment items are present (set to 0 if missing)
                for item in items_list:
                    if item not in filtered_inventory:
                        filtered_inventory[item] = 0
                        
                logger.debug(f"Filtered inventory for {agent_config['agent_id']}: {filtered_inventory}")
                
                # Choose random desired item for now
                # TODO: Could be specified in the socket data
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
                
                # Set position
                agent.position = agent_config['position']
                agent.cell_key = agent_config['cell_key']
                
                agents.append(agent)
                
            except Exception as e:
                logger.error(f"Failed to create agent {agent_config['agent_id']}: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                continue
                
        logger.info(f"Created {len(agents)} trading agents")
        return agents
        
    def _start_simulation_with_data(self, data: Dict[str, Any]):
        """
        Start the trading simulation with provided data.
        
        Args:
            data: Simulation data containing botInventoryMap
        """
        if self.simulation_running:
            logger.warning("Simulation already running, stopping previous simulation")
            self.stop_simulation()
            
        # Parse bot inventory data
        bot_inventory_map = data.get('botInventoryMap', {})
        if not bot_inventory_map:
            raise ValueError("No botInventoryMap provided in simulation data")
            
        # Parse agents configuration
        agents_config = self._parse_bot_inventory_map(bot_inventory_map)
        if not agents_config:
            raise ValueError("No valid agents found in botInventoryMap")
            
        # Create trading environment
        self.env = TradingEnvironment(self.config)
        
        # Create agents from configuration
        agents = self._create_agents_from_config(agents_config)
        
        # Initialize environment with custom agents
        self.env.agents = agents
        self.env.population_size = len(agents)
        
        # Initialize agent positions
        for agent in agents:
            self.env.agent_positions[agent.agent_id] = agent.position
            
        # Start simulation in separate thread
        self.simulation_running = True
        self.simulation_thread = threading.Thread(target=self._run_simulation)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
        # Notify server that simulation started
        self.sio.emit('simulation_started', {
            'agents_count': len(agents),
            'items': list(self.config['environment']['items_list'])
        }, namespace='/model')
        
    def _run_simulation(self):
        """Run the trading simulation loop."""
        logger.info("Starting trading simulation...")
        
        try:
            timestep = 0
            while self.simulation_running and self.env:
                # Execute one simulation step
                step_info = self._execute_simulation_step(timestep)
                
                # Emit trade data if trades occurred
                if step_info['trades_executed'] > 0:
                    self._emit_trade_data(step_info, timestep)
                
                timestep += 1
                
                # Small delay to prevent overwhelming the socket
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            self.sio.emit('simulation_error', {'error': str(e)}, namespace='/model')
        finally:
            self.simulation_running = False
            logger.info("Simulation stopped")
            
    def _execute_simulation_step(self, timestep: int) -> Dict[str, Any]:
        """
        Execute one step of the simulation.
        
        Args:
            timestep: Current timestep number
            
        Returns:
            Step information including trades
        """
        # Execute environment step
        step_info = self.env.step()
        
        # Add timestep info
        step_info['timestep'] = timestep
        step_info['generation'] = self.env.current_generation
        
        return step_info
        
    def _emit_trade_data(self, step_info: Dict[str, Any], timestep: int):
        """
        Emit trade data to the Socket.IO server.
        
        Args:
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
            
            # Get recent trades from environment
            if hasattr(self.env, 'trade_history') and self.env.trade_history:
                # Get trades from this timestep
                recent_trades = []
                for trade in self.env.trade_history[-step_info['trades_executed']:]:
                    # Extract trade data from environment format
                    # Environment stores: {'requester_gave': (item, amount), 'requester_received': (item, amount)}
                    requester_gave = trade.get('requester_gave', (None, None))
                    requester_received = trade.get('requester_received', (None, None))
                    
                    trade_formatted = {
                        'requester_id': trade.get('requester_id'),
                        'target_id': trade.get('target_id'),
                        'item_given': requester_gave[0] if requester_gave else None,
                        'amount_given': requester_gave[1] if requester_gave else None,
                        'item_received': requester_received[0] if requester_received else None,
                        'amount_received': requester_received[1] if requester_received else None,
                        'requester_cell': getattr(self._get_agent_by_id(trade.get('requester_id')), 'cell_key', None),
                        'target_cell': getattr(self._get_agent_by_id(trade.get('target_id')), 'cell_key', None)
                    }
                    
                    # Debug log the trade formatting
                    logger.debug(f"Raw trade data: {trade}")
                    logger.debug(f"Formatted trade: {trade_formatted}")
                    
                    recent_trades.append(trade_formatted)
                
                trade_data['trades'] = recent_trades
            
            # Emit trade data to /model namespace
            self.sio.emit('trade', trade_data, namespace='/model')
            logger.debug(f"Emitted {len(trade_data['trades'])} trades for timestep {timestep}")
            
        except Exception as e:
            logger.error(f"Failed to emit trade data: {e}")
            
    def _get_agent_by_id(self, agent_id: str) -> TradingAgent:
        """Get agent by ID."""
        if not self.env or not agent_id:
            return None
            
        for agent in self.env.agents:
            if agent.agent_id == agent_id:
                return agent
        return None
        
    def stop_simulation(self):
        """Stop the running simulation."""
        if self.simulation_running:
            logger.info("Stopping simulation...")
            self.simulation_running = False
            
            if self.simulation_thread and self.simulation_thread.is_alive():
                self.simulation_thread.join(timeout=5.0)
                
            self.env = None
            
            # Notify server
            if self.sio.connected:
                self.sio.emit('simulation_stopped', {}, namespace='/model')


def main():
    """Main function for testing the socket client."""
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get socket URL from command line or use default ngrok URL
    socket_url = sys.argv[1] if len(sys.argv) > 1 else 'https://geographical-clonic-jimena.ngrok-free.dev/model'
    
    # Create and connect client
    client = SocketSimulationClient(socket_url)
    
    if client.connect():
        logger.info("Socket client connected successfully")
        logger.info("Waiting for start_simulation command...")
        
        try:
            # Keep the client running
            logger.info("Waiting for start_simulation command...")
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            client.disconnect()
    else:
        logger.error("Failed to connect to socket server")
        sys.exit(1)


if __name__ == "__main__":
    main()
