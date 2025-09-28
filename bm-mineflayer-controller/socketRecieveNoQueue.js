const { io } = require('socket.io-client');
const { simulationClass } = require('./simulationClass');


class SimulationSocketClient {
  constructor() {
    this.socket = null;
    this.currentSimulation = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 5000; // 5 seconds

    // Simulation class gets created in the handleStartSimulation function
    this.currentSimulation = null;
    
    this.connect();
  }

  connect() {
    console.log('[Socket] Attempting to connect to server...');
    
    this.socket = io('https://frondescent-cherrie-semipreserved.ngrok-free.dev/mineflayer', {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: this.reconnectDelay,
      reconnectionAttempts: this.maxReconnectAttempts,
      timeout: 10000, // 10 second timeout
    });

    this.setupEventHandlers();
  }

  setupEventHandlers() {
    this.socket.on('connect', () => {
      console.log('[Socket] ✅ Connected to server');
      this.isConnected = true;
      this.reconnectAttempts = 0;
      
    });

    this.socket.on('disconnect', (reason) => {
      console.log(`[Socket] ❌ Disconnected from server: ${reason}`);
      this.isConnected = false;
      
      if (reason === 'io server disconnect') {
        // Server disconnected us, try to reconnect
        console.log('[Socket] Server disconnected client, attempting to reconnect...');
        setTimeout(() => this.connect(), this.reconnectDelay);
      }
    });

    this.socket.on('connect_error', (error) => {
      console.log(`[Socket] ⚠️ Connection error:`, error.message);
      this.reconnectAttempts++;
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.log(`[Socket] Max reconnection attempts (${this.maxReconnectAttempts}) reached`);
      }
    });

    // Important event to listen for
    this.socket.on('start_simulation', (initData) => {
      console.log('[Socket] 🚀 Received start simulation command');
      console.log('[Socket] Simulation data:', initData);
      
      this.handleStartSimulation(initData);
    });

    this.socket.on('stopSimulation', () => {
      console.log('[Socket] 🛑 Received stop simulation command');
      this.handleStopSimulation();
    });

    // DISABLED
    // this.socket.on('trade', (tradeData) => {
    //   console.log('[Socket] 💰 Received trade command:', tradeData);
    //   this.handleTradeCommand(tradeData);
    // });
  }

  async handleStartSimulation(initData) {
    try {
      // Stop any existing simulation
      if (this.currentSimulation) {
        console.log('[Socket] Stopping existing simulation...');
        await this.stopCurrentSimulation();
      }

      // create the grid
      const grid = []
      for (let i = 0; i < 10; i++) {
        const row = []
        for (let j = 0; j < 10; j++) {
            row.push(0)
        }
        grid.push(row)
      }

      // Extract the keys and parse into numbers
      const coords = Object.keys(initData.botInventoryMap || {}).map(key => {
          const [x, y] = key.split("-").map(Number);
          return [x, y];
      });
      for (const [x, y] of coords) {
        grid[x][y] = 1;
      }

      // Prase simulation parameters to determine where the 1's are
      // only the grid will work
      // everything else is default value
      initData['botInventoryMap']
      const config = {
        host: initData.host || 'mcpanel.blockwarriors.ai',
        port: initData.port || 25565,
        version: initData.version || '1.20.6',
        auth: initData.auth || 'offline',
        usernames: initData.usernames || Array.from({length: 10}, (_, i) => `Bot${i+1}`),
        grid: grid || this.createDefaultGrid(),
        base: initData.base || { x: -13.5, y: -60, z: -13.5 },
        spacing: initData.spacing || (27/9)
      };

      console.log('[Socket] Creating simulation with config:', config);
      
      // Start spawning bots
      console.log('[Socket] Spawning bots from grid...');
      this.currentSimulation = new simulationClass(config);


        setTimeout(() => {
          for (let phase = 0; phase < 100; phase++) {
      
              const items = ['apple', 'gold_ingot', 'diamond', 'emerald', 'redstone', 'apple', 'gold_ingot', 'diamond', 'emerald', 'redstone'];
              
              setTimeout(() => {
                this.currentSimulation.trade_timestep(items);
              }, 1000 + phase * 9500);
            }
          
        }, 5000);

      // Wait for bots to be ready, then start trading phases
    //   await this.sleep(5000); // Give bots time to spawn and get to positions
      
      console.log('[Socket] Starting trading phases...');
      
    //   await this.startTradingPhases(initData.phases || 4, initData.phaseDelay || 9500);
      
      console.log('[Socket] ✅ Simulation completed');

    } catch (error) {
      console.error('[Socket] ❌ Simulation error:', error);
    }
  }


  async handleStopSimulation() {
    if (this.currentSimulation) {
      await this.stopCurrentSimulation();
    } else {
    }
  }

  async stopCurrentSimulation() {
    if (!this.currentSimulation) return;
    
    console.log('[Socket] Cleaning up current simulation...');
    
    // Clear trade queue when stopping simulation
    // DISABLED
    // const clearedTrades = this.clearTradeQueue();
    // if (clearedTrades > 0) {
    //   console.log(`[Socket] Cleared ${clearedTrades} pending trades from queue`);
    // }
    
    // Disconnect all bots
    if (this.currentSimulation.bots) {
      for (const bot of this.currentSimulation.bots) {
        try {
          bot.end();
        } catch (err) {
          console.log(`[Socket] Error disconnecting bot ${bot.username}:`, err.message);
        }
      }
    }
    
    this.currentSimulation = null;
  }


  createDefaultGrid() {
    // Create a 10x10 grid with bots at specific positions
    const grid = Array(10).fill().map(() => Array(10).fill(0));
    
    // Place bots at corners and strategic positions
    grid[9][0] = 1;  // Bottom-left
    grid[9][9] = 1;  // Bottom-right
    grid[0][0] = 1;  // Top-left
    grid[0][9] = 1;  // Top-right
    grid[5][4] = 1;  // Center-left
    grid[5][5] = 1;  // Center-right
    grid[2][2] = 1;  // Upper-left
    grid[8][8] = 1;  // Lower-right
    grid[2][8] = 1;  // Upper-right
    grid[8][2] = 1;  // Lower-left
    
    return grid;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }



}

// Create and start the socket client
console.log('[Socket] Starting simulation socket client...');
const client = new SimulationSocketClient();

// Graceful shutdown handling
process.on('SIGINT', async () => {
  console.log('\n[Socket] Shutting down gracefully...');
  
  // Stop queue processor
  // DISABLED
  // client.stopQueueProcessor();
  
  if (client.currentSimulation) {
    await client.stopCurrentSimulation();
  }
  
  if (client.socket) {
    client.socket.disconnect();
  }
  
  process.exit(0);
});

module.exports = { SimulationSocketClient };