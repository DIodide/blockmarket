const { io } = require('socket.io-client');
const { simulationClass } = require('./simulationClass');

// Add shuffle method to Array prototype
Array.prototype.shuffle = function() {
  for (let i = this.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [this[i], this[j]] = [this[j], this[i]];
  }
  return this;
};

class SimulationSocketClient {
  constructor() {
    this.socket = null;
    this.currentSimulation = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 5000; // 5 seconds
    
    // Trade queue system
    this.tradeQueue = [];
    this.isProcessingTrades = false;
    this.queueProcessInterval = 2000; // Process queue every 2 seconds
    this.queueTimer = null;
    this.maxBatchSize = 10; // Max trades to process per batch

    // Simulation class gets created in the handleStartSimulation function
    this.currentSimulation = null;
    
    this.connect();
    this.startQueueProcessor();
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
      
      // Send initial status
      this.sendStatus('connected', 'Client connected and ready for simulation commands');
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

    this.socket.on('getStatus', () => {
      console.log('[Socket] 📊 Received status request');
      this.handleGetStatus();
    });

    this.socket.on('trade', (tradeData) => {
      console.log('[Socket] 💰 Received trade command:', tradeData);
      this.handleTradeCommand(tradeData);
    });
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
      this.sendStatus('starting', 'Creating simulation instance...');
      
      // Start spawning bots
      console.log('[Socket] Spawning bots from grid...');
      this.sendStatus('spawning', 'Spawning bots onto the grid...');
      this.currentSimulation = new simulationClass(config);

      // Wait for bots to be ready, then start trading phases
    //   await this.sleep(5000); // Give bots time to spawn and get to positions
      
      console.log('[Socket] Starting trading phases...');
      this.sendStatus('trading', 'Starting automated trading phases...');
      
    //   await this.startTradingPhases(initData.phases || 4, initData.phaseDelay || 9500);
      
      this.sendStatus('completed', 'Simulation completed successfully');
      console.log('[Socket] ✅ Simulation completed');

    } catch (error) {
      console.error('[Socket] ❌ Simulation error:', error);
      this.sendStatus('error', `Simulation failed: ${error.message}`);
    }
  }

  async startTradingPhases(numPhases, phaseDelay) {
    const botNames = Array.from({length: 10}, (_, i) => `Bot${i+1}`);
    
    for (let phase = 0; phase < numPhases; phase++) {
      console.log(`[Socket] Starting trading phase ${phase + 1}/${numPhases}`);
      this.sendStatus('trading', `Running trading phase ${phase + 1}/${numPhases}`);

      // Shuffle bot names for random trading pairs
      const shuffledBots = [...botNames];
      for (let i = shuffledBots.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffledBots[i], shuffledBots[j]] = [shuffledBots[j], shuffledBots[i]];
      }

      // Start multiple trades simultaneously
      const tradePromises = [];
      for (let i = 0; i < shuffledBots.length - 1; i += 2) {
        const bot1 = shuffledBots[i];
        const bot2 = shuffledBots[i + 1];
        tradePromises.push(
          this.currentSimulation.trade(bot1, 'diamond_sword', bot2, 'emerald')
        );
      }

      // Wait for all trades in this phase to complete
      await Promise.all(tradePromises);
      
      // Wait before next phase (except for the last phase)
      if (phase < numPhases - 1) {
        await this.sleep(phaseDelay);
      }
    }
  }

  async handleStopSimulation() {
    if (this.currentSimulation) {
      await this.stopCurrentSimulation();
      this.sendStatus('stopped', 'Simulation stopped by server command');
    } else {
      this.sendStatus('idle', 'No active simulation to stop');
    }
  }

  async stopCurrentSimulation() {
    if (!this.currentSimulation) return;
    
    console.log('[Socket] Cleaning up current simulation...');
    
    // Clear trade queue when stopping simulation
    const clearedTrades = this.clearTradeQueue();
    if (clearedTrades > 0) {
      console.log(`[Socket] Cleared ${clearedTrades} pending trades from queue`);
    }
    
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

  handleGetStatus() {
    const queueStatus = this.getQueueStatus();
    const status = {
      connected: this.isConnected,
      hasActiveSimulation: !!this.currentSimulation,
      botCount: this.currentSimulation ? this.currentSimulation.bots.length : 0,
      tradeQueue: queueStatus,
      timestamp: new Date().toISOString()
    };
    
    this.socket.emit('statusResponse', status);
  }

  sendStatus(status, message, data = {}) {
    if (!this.isConnected) return;
    
    const statusData = {
      status,
      message,
      timestamp: new Date().toISOString(),
      ...data
    };
    
    console.log(`[Socket] 📡 Sending status: ${status} - ${message}`);
    this.socket.emit('simulationStatus', statusData);
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

  /**
   * Handle incoming trade commands by adding them to the queue
   * @param {Object} tradeData - Trade command data from server
   */
  handleTradeCommand(tradeData) {
    // Validate trade data format
    console.log('[Socket] trade data format:', tradeData);

    // Add timestamp to trade for queue management
    const queuedTrade = {
      items: [],
      queuedAt: Date.now(),
      id: this.generateTradeId()
    };

    const trades = tradeData['trades'];
    const keys = [];
    for (const trade of trades) {
        keys.push(trade['request_id']);
        queuedTrade['items'].push(trade['item_given']);
        queuedTrade['items'].push(trade['item_received']);
    }

    queuedTrade['items'].shuffle();

    this.tradeQueue.push(queuedTrade);
    
    console.log(`[Socket] 📝 Trade queued (ID: ${queuedTrade.id}). Queue length: ${this.tradeQueue.length}`);
    
    // Send status update about queue state
    this.sendStatus('trade_queued', `Trade queued. Queue length: ${this.tradeQueue.length}`, {
      queueLength: this.tradeQueue.length,
      tradeId: queuedTrade.id
    });
  }

  /**
   * Validate incoming trade data format
   * @param {Object} tradeData - Trade data to validate
   * @returns {boolean} True if valid
   */
  validateTradeData(tradeData) {
    // Check for new format with tradeData.trades array
    if (tradeData && tradeData.tradeData && Array.isArray(tradeData.tradeData.trades)) {
      return tradeData.tradeData.trades.every(trade => 
        trade &&
        typeof trade.request_id === 'string' &&
        typeof trade.item_given === 'string' &&
        typeof trade.item_received === 'string'
      );
    }
    
    // Check for legacy format: { bot1: "Bot1", item1: "diamond_sword", bot2: "Bot2", item2: "emerald" }
    // or array format: [{ bot1: "Bot1", item1: "diamond_sword", bot2: "Bot2", item2: "emerald" }, ...]
    if (Array.isArray(tradeData)) {
      return tradeData.every(trade => this.validateSingleTrade(trade));
    } else {
      return this.validateSingleTrade(tradeData);
    }
  }

  /**
   * Validate a single trade object
   * @param {Object} trade - Single trade object
   * @returns {boolean} True if valid
   */
  validateSingleTrade(trade) {
    return trade && 
           typeof trade.bot1 === 'string' && 
           typeof trade.item1 === 'string' && 
           typeof trade.bot2 === 'string' && 
           typeof trade.item2 === 'string';
  }

  /**
   * Generate a unique trade ID
   * @returns {string} Unique trade ID
   */
  generateTradeId() {
    return `trade_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Start the queue processor that runs at regular intervals
   */
  startQueueProcessor() {
    if (this.queueTimer) {
      clearInterval(this.queueTimer);
    }

    this.queueTimer = setInterval(() => {
      this.processTradeQueue();
    }, this.queueProcessInterval);

    console.log(`[Socket] 🔄 Trade queue processor started (interval: ${this.queueProcessInterval}ms)`);
  }

  /**
   * Stop the queue processor
   */
  stopQueueProcessor() {
    if (this.queueTimer) {
      clearInterval(this.queueTimer);
      this.queueTimer = null;
      console.log('[Socket] ⏹️ Trade queue processor stopped');
    }
  }

  /**
   * Process all queued trades in the current timestep
   */
  async processTradeQueue() {
    // Skip if already processing trades or no simulation active
    if (this.isProcessingTrades || !this.currentSimulation || this.tradeQueue.length === 0) {
      return;
    }

    this.isProcessingTrades = true;
    
    try {
      // Check if queue is empty
      if (this.tradeQueue.length === 0) {
        return;
      }

      // Take trades from queue
      const trades = this.tradeQueue.pop();
      
      if (!trades || !trades.items) {
        console.log('[Socket] ⚠️ Invalid trade data from queue');
        return;
      }

      const items = trades.items;
      
      console.log(`[Socket] 🎯 Processing ${items.length} items from queue:`, items);

      await this.currentSimulation.trade_timestep(items);

      console.log(`[Socket] ✅ Completed processing trades from queue`);

    } catch (error) {
      console.error('[Socket] ❌ Error processing trade queue:', error);
      this.sendStatus('error', `Trade processing failed: ${error.message}`);
    } finally {
      this.isProcessingTrades = false;
    }
  }

  /**
   * Execute a batch of trades in parallel
   * @param {Array} trades - Array of trade objects to execute
   */
  async executeTradeBatch(trades) {
    const tradePromises = [];

    for (const trade of trades) {
      try {
        // Convert to single trade format if it's an array
        const singleTrades = Array.isArray(trade) ? trade : [trade];
        
        for (const singleTrade of singleTrades) {
          const { bot1, item1, bot2, item2 } = singleTrade;
          
          console.log(`[Socket] 🤝 Executing trade: ${bot1}(${item1}) <-> ${bot2}(${item2})`);
          
          // Add trade promise to batch
          const tradePromise = this.currentSimulation.trade(bot1, item1, bot2, item2)
            .then(() => {
              console.log(`[Socket] ✅ Trade completed: ${bot1}(${item1}) <-> ${bot2}(${item2})`);
            })
            .catch((error) => {
              console.error(`[Socket] ❌ Trade failed: ${bot1}(${item1}) <-> ${bot2}(${item2}) - ${error.message}`);
            });
            
          tradePromises.push(tradePromise);
        }
      } catch (error) {
        console.error('[Socket] ❌ Error preparing trade:', error);
      }
    }

    // Wait for all trades to complete
    if (tradePromises.length > 0) {
      await Promise.all(tradePromises);
    }
  }

  /**
   * Clear the trade queue (useful for cleanup or reset)
   */
  clearTradeQueue() {
    const clearedCount = this.tradeQueue.length;
    this.tradeQueue = [];
    console.log(`[Socket] 🗑️ Cleared ${clearedCount} trades from queue`);
    return clearedCount;
  }

  /**
   * Get current queue status
   * @returns {Object} Queue status information
   */
  getQueueStatus() {
    return {
      queueLength: this.tradeQueue.length,
      isProcessing: this.isProcessingTrades,
      processInterval: this.queueProcessInterval,
      maxBatchSize: this.maxBatchSize
    };
  }
}

// Create and start the socket client
console.log('[Socket] Starting simulation socket client...');
const client = new SimulationSocketClient();

// Graceful shutdown handling
process.on('SIGINT', async () => {
  console.log('\n[Socket] Shutting down gracefully...');
  
  // Stop queue processor
  client.stopQueueProcessor();
  
  if (client.currentSimulation) {
    await client.stopCurrentSimulation();
  }
  
  if (client.socket) {
    client.socket.disconnect();
  }
  
  process.exit(0);
});

module.exports = { SimulationSocketClient };